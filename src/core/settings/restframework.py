from datetime import timedelta

from .environments import SECRET_KEY

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("authorization", ""),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken", ),
    "TOKEN_TYPE_CLAIM": "token_type",
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_PAGINATION_CLASS":
    "core.middlewares.PaginationMiddleware"
}

# if not DEBUG:
REST_FRAMEWORK["EXCEPTION_HANDLER"] = "core.middlewares.core_exception_handler"

JAZZMIN_SETTINGS = {
    "site_title":
    "TLT",
    "site_header":
    "TLT",
    "site_brand":
    "TLT",
    "topmenu_links": [
        {
            "name": "Home",
            "url": "admin:index",
            "permissions": ["auth.view_user"]
        },
        {
            "app": "content"
        },
    ],
    "usermenu_links": [{
        "model": "auth.user"
    }],
    "show_sidebar":
    True,
    "navigation_expanded":
    False,
    "hide_apps": ['auth'],
    "hide_models": [],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    "default_icon_parents":
    "fas fa-chevron-circle-right",
    "default_icon_children":
    "fas fa-circle",
    "related_modal_active":
    False,
    "custom_css":
    None,
    "custom_js":
    None,
    "show_ui_builder":
    False,
    "changeform_format":
    "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs"
    },
    "language_chooser":
    False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-warning",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "cyborg",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-outline-info",
        "warning": "btn-outline-warning",
        "danger": "btn-outline-danger",
        "success": "btn-outline-success"
    }
}
