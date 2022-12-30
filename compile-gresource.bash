#!/usr/bin/env bash

glib-compile-resources --target=app/com.github.ZandronumLauncher.gresource com.github.ZandronumLauncher.gresource.xml

gresource list app/com.github.ZandronumLauncher.gresource
