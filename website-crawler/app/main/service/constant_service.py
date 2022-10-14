import time
import datetime

from app.main.constant import paths


class ConstantService:
    @staticmethod
    def fetched_scraped_data():
        return paths.SCRAPPED_PATH + '/' + datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

    @staticmethod
    def fetched_scraped_histroy():
        return paths.HISTORY_PATH + '/'

    @staticmethod
    def histroy_path():
        return paths.HISTORY_PATH

    @staticmethod
    def cc_mail_id():
        return ""

    @staticmethod
    def data_in_path():
        return paths.IN_PATH

    @staticmethod
    def data_processed_path():
        return paths.PROCESSED_PATH

    @staticmethod
    def log_path():
        return paths.LOG_PATH

    @staticmethod
    def server_host():
        return paths.SERVER_HOST

    @staticmethod
    def get_menu_class():
        # Class of menu, should be same for all menu.
        return [
            'Dropdown',
            'dropdown',
            'header-nav-item',
            'Header-nav-inner',
            'nav-dropdown',
            'navbar__item',
            'header-nav-item--folder',
            'element-select',
            'nav-item',
            'folder',
            'item',
            'has-dropdown',
            'nav-parent',
            'menu-item-has-children',
            'cmp-navigation__item',
            'about-us-container',
            'parent',
            'nav-element',
            'srf-dropdown',
            'menu-item-has-items',
            'navlink',
            'sc-bdvvaa',
            'et_pb_column',
            'group',
            'menu-header',
            'uaUDY',
            'nav-items-container',
            'tn-menuitem-wrapper',
            'nav-dropdown-item',
            'sb-navlinkh',
        ]

    @staticmethod
    def get_menu_name_wrapper_class():
        # If menu name wrap in separate tag with class.
        return [
            'wrap',
            'folder-toggle',
        ]

    @staticmethod
    def get_menu_item_wrapper_class():
        # Class of menu items
        return [
            'dropdown-wrapper',
            'navbar__submenu',
            'header-nav-folder-item',
            'dropdown-content',
            'dropdown-item',
            'header-nav-folder-content',
            'dropdown-menu',
            'element-select-option-content',
            'subnav',
            'submenu-group',
            'navbar-dropdown',
            'nav-children',
            'menu-item',
            'cmp-navigation__group',
            'products-children',
            'child',
            'nav-element',
            'srf-dropdown-menu-grid',
            'srf-dropdown-menu',
            'mega-menu-subnav',
            'dropdown',
            'mega-menu-subnav',
            'dropdown-menu',
            'menu-effect',
            'menu-service',
            'menu-event',
            'customMenuDrawerWrapper',
            'nav-item',
            'tn-submenu-wrapper',
            'drop-downl-list',
            'sb-navdd',
        ]

    @staticmethod
    def get_js_page_identifier():
        return [
            'loading...',
            'need to enable javascript',
            'without javascript enabled',
            'necessary to enable javascript',
            'frame or with javascript disabled',
            'sorry to interrupt css error refresh',
            'you have been blocked',
            'javascript is required',
            'please turn javascript on',
            'your action cannot be completed due to security constraints',
            'if you are not redirected automatically',
        ]

    @staticmethod
    def get_not_ok_title():
        return [
            'access denied',
            '403 forbidden',
        ]

    @staticmethod
    def get_all_search_engines():
        return [
            'google.com',
            'yahoo.com',
            'bing.com',
            'duckduckgo.com'
        ]
