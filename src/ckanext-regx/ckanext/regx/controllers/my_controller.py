from ckan.lib.base import BaseController, render


class RegxController(BaseController):
    def index(self):
        # Pass data to the template
        return render('index.html', extra_vars={'message': 'Hello, CKAN from Regx Plugin!'})
