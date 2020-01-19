# -*- coding: utf-8 -*-
# filename: indexPage.py

import web
import os

self_dir = os.path.dirname(os.path.abspath(__file__))

class indexPage(object):
    def GET(self):
        render = web.template.render('templates')
        return render.indexPage()