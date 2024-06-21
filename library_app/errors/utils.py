from flask import render_template
from flask_login import current_user


def render_error_template(error):
    if not current_user.is_authenticated:
        return render_template(f"errors/{error}.html", cat="main"), error
    elif current_user.get_urole() == "user":
        return (
            render_template(
                f"errors/{error}.html", title="Error", user=current_user, cat="user"
            ),
            error,
        )
    else:
        return (
            render_template(
                f"errors/{error}.html",
                title="Error",
                librarian=current_user,
                cat="librarian",
            ),
            error,
        )
