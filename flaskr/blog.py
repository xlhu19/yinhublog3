from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import *
import markdown
from flask import Markup
import uuid

bp = Blueprint('blog', __name__)

#####################
# The index page
#####################
@bp.route('/')
def index():
  db = get_db()
  posts = db.execute(
    'SELECT p.uuid, title, body, created, updated, author_id, username, tags'
    ' FROM post p JOIN user u ON p.author_id = u.id'
    ' ORDER BY updated DESC'
  ).fetchall()

  return render_template('blog/index.html', posts=posts)

@bp.route('/<uuid>')
def get_post_by_uuid(uuid):
  p = get_post(uuid, check_author=False)
  pp = {}
  for key in p.keys():
      pp[key] = p[key]
  pp['body'] = Markup(markdown.markdown(p['body'],
      output_format='html5',
      extensions=['markdown.extensions.toc',
      'markdown.extensions.sane_lists',
      'markdown.extensions.codehilite',
      'markdown.extensions.abbr',
      'markdown.extensions.attr_list',
      'markdown.extensions.def_list',
      'markdown.extensions.fenced_code',
      'markdown.extensions.footnotes',
      'markdown.extensions.smart_strong',
      'markdown.extensions.meta',
      'markdown.extensions.nl2br',
      'markdown.extensions.tables']
  ))

  return render_template('blog/blog.html', post=pp)

def get_post(uuid, check_author=True):
    post = get_db().execute(
        'SELECT p.uuid, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.uuid = ?',
        (uuid,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
  if request.method == 'POST':
    new_uuid = str(uuid.uuid1())
    title = request.form['title']
    body = request.form['body']
    tags = ""
    error = None

    if not title:
      error = 'Title is required.'

    if error is not None:
      flash(error)
    else:
      update_db({'uuid':new_uuid,
                 'title':title,
                 'body':body,
                 'tags':tags,
                 'author_id':g.user['id'],}, "insert")
      return redirect(url_for('blog.get_post_by_uuid', uuid=new_uuid))

  return render_template('blog/create.html')


@bp.route('/<uuid>/update', methods=('GET', 'POST'))
@login_required
def update(uuid):
    """Update a post if the current user is the author."""
    post = get_post(uuid)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = ""

        error = None

        if not title:
          error = 'Title is required.'

        if error is not None:
          flash(error)
        else:
          update_db({'title':title,
                     'body':body,
                     'author_id':g.user['id'],
                     'tags':tags,
                     'uuid':uuid}, "update")

          return redirect(url_for('blog.get_post_by_uuid', uuid=uuid))

    return render_template('blog/update.html', post=post)


@bp.route('/<uuid>/delete', methods=('POST',))
@login_required
def delete(uuid):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(uuid)
    db = get_db()
    db.execute('DELETE FROM post WHERE uuid = ?', (uuid,))
    db.commit()
    return redirect(url_for('blog.index'))

