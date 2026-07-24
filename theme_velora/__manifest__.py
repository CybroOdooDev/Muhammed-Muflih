# -*- coding: utf-8 -*-
{
    "name": "Theme Velora",
    "version": "18.0.1.0.0",
    "category": "Theme/eCommerce",
    "summary": "Luxury perfume eCommerce theme for Odoo Website",
    "description": "Velora is a luxury fragrance storefront theme with a refined homepage, animated product showcase, collection sections, testimonials, FAQ, and newsletter interactions.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["website", "website_sale", "website_sale_wishlist"],
    "data": [
        "data/categories.xml",
        "data/website_menu.xml",
        "views/layout_templates.xml",
        "views/snippets/snippets.xml",
        "views/snippets/options.xml",
        "views/homepage_templates.xml",
        "views/contact_templates.xml",
        "views/about_templates.xml",
        "views/collections_templates.xml",
        "views/bestseller_templates.xml",
        "views/confirmation_templates.xml",
        "views/login_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "theme_velora/static/src/css/style.css",
            "theme_velora/static/src/css/bestseller.css",
            "theme_velora/static/src/css/confirmation.css",
            "theme_velora/static/src/js/theme_velora.js"
        ],
        "website.assets_wysiwyg": [
            "theme_velora/static/src/css/style.css"
        ]
    },
    "images": ["static/description/banner.webp"],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
