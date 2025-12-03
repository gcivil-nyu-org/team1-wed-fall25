from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Max, Exists, OuterRef
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Conversation, PrivateMessage, UserOnlineStatus, ConversationHidden
from .forms import MessageForm


@login_required
def inbox(request):
    """Display list of all conversations for the current user"""
    user = request.user

    # Get hidden info for this user (conversation_id -> hidden_at)
    hidden_info = {
        h.conversation_id: h.hidden_at
        for h in ConversationHidden.objects.filter(user=user)
    }

    # Get all conversations where user is participant
    conversations = (
        Conversation.objects.filter(Q(user1=user) | Q(user2=user))
        .select_related("user1", "user2")
        .annotate(
            last_message_time=Max("private_messages__created_at"),
        )
        .order_by("-last_message_time")
    )

    # Prepare conversation data with other user info
    conversation_list = []
    for conv in conversations:
        # Check if this conversation is hidden and has no new messages after hidden_at
        if conv.id in hidden_info:
            hidden_at = hidden_info[conv.id]
            # Check if there are new messages after hidden_at
            has_new_messages = conv.private_messages.filter(
                created_at__gt=hidden_at
            ).exists()
            if not has_new_messages:
                # No new messages since hiding, skip this conversation
                continue

        other_user = conv.get_other_user(user)

        # Get last message (considering hidden_at for display)
        if conv.id in hidden_info:
            # Only show last message if it's after hidden_at
            last_message = (
                conv.private_messages.filter(created_at__gt=hidden_info[conv.id])
                .order_by("-created_at")
                .first()
            )
        else:
            last_message = conv.get_last_message()

        # Calculate unread count (considering hidden_at)
        if conv.id in hidden_info:
            unread_count = (
                conv.private_messages.filter(
                    is_read=False, created_at__gt=hidden_info[conv.id]
                )
                .exclude(sender=user)
                .count()
            )
        else:
            unread_count = (
                conv.private_messages.filter(is_read=False).exclude(sender=user).count()
            )

        # Get online status
        try:
            online_status = other_user.online_status.is_online
        except UserOnlineStatus.DoesNotExist:
            online_status = False

        conversation_list.append(
            {
                "conversation": conv,
                "other_user": other_user,
                "last_message": last_message,
                "unread_count": unread_count,
                "is_online": online_status,
            }
        )

    context = {
        "conversations": conversation_list,
        "has_conversations": len(conversation_list) > 0,
    }

    return render(request, "messages/inbox.html", context)


@login_required
def conversation_detail(request, user_id):
    """Display conversation with a specific user"""
    user = request.user
    other_user = get_object_or_404(User, id=user_id)

    if user == other_user:
        return redirect("user_messages:inbox")

    # Get or create conversation
    conversation, created = Conversation.get_or_create_conversation(user, other_user)

    # If coming from event page with from_event=true, auto-hide previous messages
    # This ensures the user starts with a fresh conversation view
    from_event = request.GET.get("from_event") == "true"
    if from_event and not created:
        # Check if there are existing messages and no current hidden record
        existing_hidden = ConversationHidden.objects.filter(
            conversation=conversation, user=user
        ).first()
        if not existing_hidden and conversation.private_messages.exists():
            # Create hidden record with current time to hide previous messages
            ConversationHidden.objects.create(conversation=conversation, user=user)

    # Check if user has hidden this conversation (for filtering messages)
    user_hidden = ConversationHidden.objects.filter(
        conversation=conversation, user=user
    ).first()

    # Mark all messages from other user as read
    # (only those after hidden_at if applicable)
    messages_to_mark = PrivateMessage.objects.filter(
        conversation=conversation, sender=other_user, is_read=False
    )
    if user_hidden:
        messages_to_mark = messages_to_mark.filter(created_at__gt=user_hidden.hidden_at)
    messages_to_mark.update(is_read=True)

    # Get chat messages (only those after hidden_at if user had hidden the conversation)
    chat_messages = conversation.private_messages.select_related("sender")
    if user_hidden:
        chat_messages = chat_messages.filter(created_at__gt=user_hidden.hidden_at)
    chat_messages = chat_messages.order_by("created_at")

    # Get online status
    try:
        is_online = other_user.online_status.is_online
    except UserOnlineStatus.DoesNotExist:
        is_online = False

    # Handle message submission
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = user
            message.save()

            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save(update_fields=["updated_at"])

            # Note: We don't delete sender's hidden record
            # to preserve the hidden_at filter
            # This ensures only messages after hidden_at are shown

            # Return JSON for AJAX requests
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "status": "success",
                        "message": {
                            "id": message.id,
                            "content": message.content,
                            "sender": user.username,
                            "created_at": message.created_at.strftime("%I:%M %p"),
                            "is_mine": True,
                        },
                    }
                )

            return redirect("user_messages:conversation", user_id=user_id)
    else:
        form = MessageForm()

    context = {
        "conversation": conversation,
        "other_user": other_user,
        "chat_messages": chat_messages,
        "form": form,
        "is_online": is_online,
    }

    return render(request, "messages/conversation.html", context)


@login_required
def user_list(request):
    """Display list of all users to start a conversation with"""
    user = request.user

    # Get all users except current user
    users = (
        User.objects.exclude(id=user.id)
        .select_related("profile")
        .annotate(
            has_conversation=Exists(
                Conversation.objects.filter(
                    Q(user1=user, user2=OuterRef("pk"))
                    | Q(user2=user, user1=OuterRef("pk"))
                )
            )
        )
        .order_by("username")
    )

    # Search functionality
    search_query = request.GET.get("q", "").strip()
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Add online status to each user
    user_list_data = []
    for u in page_obj:
        try:
            is_online = u.online_status.is_online
        except UserOnlineStatus.DoesNotExist:
            is_online = False

        user_list_data.append(
            {
                "user": u,
                "is_online": is_online,
                "has_conversation": u.has_conversation,
            }
        )

    context = {
        "users": user_list_data,
        "page_obj": page_obj,
        "search_query": search_query,
    }

    return render(request, "messages/user_list.html", context)


@login_required
@require_POST
def send_message(request, user_id):
    """API endpoint to send a message (AJAX)"""
    user = request.user
    other_user = get_object_or_404(User, id=user_id)

    if user == other_user:
        return JsonResponse(
            {"status": "error", "message": "Cannot message yourself"}, status=400
        )

    content = request.POST.get("content", "").strip()
    if not content:
        return JsonResponse(
            {"status": "error", "message": "Message cannot be empty"}, status=400
        )

    # Get or create conversation
    conversation, _ = Conversation.get_or_create_conversation(user, other_user)

    # Create message
    message = PrivateMessage.objects.create(
        conversation=conversation,
        sender=user,
        content=content,
    )

    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=["updated_at"])

    # Note: We don't delete anyone's hidden record
    # - Sender's hidden_at ensures they only see messages after that time
    # - Recipient's hidden_at ensures they only see messages after that time

    return JsonResponse(
        {
            "status": "success",
            "message": {
                "id": message.id,
                "content": message.content,
                "sender": user.username,
                "created_at": message.created_at.strftime("%I:%M %p"),
                "is_mine": True,
            },
        }
    )


@login_required
def get_messages(request, user_id):
    """API endpoint to get new messages (for polling)"""
    user = request.user
    other_user = get_object_or_404(User, id=user_id)

    last_id = request.GET.get("last_id", 0)

    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    # Get conversation
    try:
        conversation = Conversation.objects.get(
            Q(user1=user, user2=other_user) | Q(user1=other_user, user2=user)
        )
    except Conversation.DoesNotExist:
        return JsonResponse({"status": "success", "messages": []})

    # Check if user has hidden this conversation
    user_hidden = ConversationHidden.objects.filter(
        conversation=conversation, user=user
    ).first()

    # Get new messages
    new_messages = conversation.private_messages.filter(id__gt=last_id).select_related(
        "sender"
    )

    # Filter by hidden_at if applicable
    if user_hidden:
        new_messages = new_messages.filter(created_at__gt=user_hidden.hidden_at)

    new_messages = new_messages.order_by("created_at")

    # Mark messages from other user as read
    new_messages.filter(sender=other_user, is_read=False).update(is_read=True)

    messages_data = []
    for msg in new_messages:
        messages_data.append(
            {
                "id": msg.id,
                "content": msg.content,
                "sender": msg.sender.username,
                "created_at": msg.created_at.strftime("%I:%M %p"),
                "is_mine": msg.sender == user,
            }
        )

    return JsonResponse({"status": "success", "messages": messages_data})


@login_required
def unread_count(request):
    """API endpoint to get total unread message count"""
    user = request.user

    # Get hidden info for this user (conversation_id -> hidden_at)
    hidden_info = {
        h.conversation_id: h.hidden_at
        for h in ConversationHidden.objects.filter(user=user)
    }

    # Get all unread messages sent to this user
    unread_messages = PrivateMessage.objects.filter(
        Q(conversation__user1=user) | Q(conversation__user2=user),
        is_read=False,
    ).exclude(sender=user)

    # Count only messages that are after hidden_at (if conversation is hidden)
    count = 0
    for msg in unread_messages:
        if msg.conversation_id in hidden_info:
            if msg.created_at > hidden_info[msg.conversation_id]:
                count += 1
        else:
            count += 1

    return JsonResponse({"status": "success", "count": count})


@login_required
@require_POST
def update_online_status(request):
    """API endpoint to update user's online status"""
    user = request.user
    status, _ = UserOnlineStatus.objects.get_or_create(user=user)
    status.set_online()

    return JsonResponse({"status": "success"})


@login_required
@require_http_methods(["DELETE", "POST"])
def delete_conversation(request, conversation_id):
    """Hide a conversation for the current user (doesn't delete for the other user)"""
    user = request.user

    conversation = get_object_or_404(
        Conversation,
        Q(user1=user) | Q(user2=user),
        id=conversation_id,
    )

    # Hide the conversation for this user
    # If already hidden, update hidden_at to current time (to hide new messages too)
    hidden, created = ConversationHidden.objects.get_or_create(
        conversation=conversation, user=user
    )
    if not created:
        # Update hidden_at to current time
        hidden.hidden_at = timezone.now()
        hidden.save(update_fields=["hidden_at"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "success"})

    return redirect("user_messages:inbox")
