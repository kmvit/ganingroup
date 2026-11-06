from django.contrib import admin

from .models import ChatMessage, ChatSession, KnowledgePage


@admin.register(KnowledgePage)
class KnowledgePageAdmin(admin.ModelAdmin):
    list_display = ('title', 'site', 'fetched_at', 'url')
    list_filter = ('site',)
    search_fields = ('title', 'content', 'url')
    readonly_fields = ('fetched_at',)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    can_delete = False
    readonly_fields = ('role', 'text', 'sources', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'site', 'consent_at', 'created_at')
    list_filter = ('site',)
    readonly_fields = ('id', 'site', 'consent_version', 'consent_at', 'created_at')
    inlines = [ChatMessageInline]

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False
