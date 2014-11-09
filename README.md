Tortilla
========

A tiny Python library for creating wrappers around external APIs.

Example:

    from tortilla import Service

    github = Service('https://api.github.com')
    users = github.endpoint('/users')

    redodo = users.get('redodo')

    print(redodo.login)  # prints "redodo"
