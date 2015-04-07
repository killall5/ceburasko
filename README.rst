=========
Ceburasko
=========

Ceburasko is simple Django app for storing crashes.

Quick start
-----------

1. Add 'ceburasko' to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'ceburasko',
    )

2. Include the ceburasko URLconf in your project urls.py like this::

    url(r'^ceburasko/', include('ceburasko.urls')),

3. Run `python manage.py migrate` to create the ceburasko models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a Project and Bug Tracker (you'll need the Admin app enabled).

5. Upload crashes to http://127.0.0.1:8000/ceburasko/project-1/upload-crash/
   in YAML format like this::

   stack:
   - pos: 0
     fn: main
     file: test.c
     line: 6
   kind: Program terminated with signal 6. Aborted.
   component: test.app
   version: 1.0

6. View crashes visiting http://127.0.0.1:8000/ceburasko/project-1/

