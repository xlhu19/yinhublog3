from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import *
import markdown
from flask import Markup
import uuid
import time
import operator
import re
# from flaskr.db_model import User, Post

bp = Blueprint('blog', __name__)

visitor = []

@bp.route('/jingdian')
def jingdian():
  return render_template('jingdian/index.html')

#####################
# The index page
#####################
@bp.route('/')
def index():
  db = get_db()
  posts = db.execute(
    'SELECT p.uuid, title, body, created, updated, author_id, username, tags,tags_index, read_cnt, good_cnt'
    ' FROM post p JOIN user u ON p.author_id = u.id'
    ' ORDER BY tags,tags_index DESC'
  ).fetchall()

  posts_n = []
  pre_tag = ''
  for p in posts:
    n = {}
    for key in p.keys():
      n[key] = p[key]
    if p['tags'] == pre_tag:
      n['tags'] = ''
    pre_tag = p['tags']

    n['tags'] = n['tags'].strip('/').replace('/', ' -> ')
    posts_n.append(n)

  return render_template('blog/index.html', posts=posts_n)

def generate_body_index(body):
  inx_1 = re.compile("^#\s[0-9]{1,2}")
  inx_2 = re.compile("^##\s[0-9]{1,2}\.[0-9]{1,2}")
  inx_3 = re.compile("^###\s[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}")
  body_with_index = body
  index = ''
  body_lines = body.split("\r\n")
  for l in body_lines:
    if inx_1.match(l):
      index += '' 
    elif inx_2.match(l):
      index += '' 
    elif inx_3.match(l):
      index += '' 
    else:
      continue 
  print(len(body_lines))
  return body_with_index

@bp.route('/<uuid>')
def get_post_by_uuid(uuid):
  p = get_post(uuid, check_author=False)
  pp = {}
  for key in p.keys():
      pp[key] = p[key]
  p_with_indx = generate_body_index(p['body'])
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


  # Check visit count
  # The same ip within one hour is counted 1 visit
  ip = request.remote_addr
  dtime = time.strftime("%Y-%m-%d-%H")
  c = {'uuid':uuid, 'ip':ip, 'time':dtime}
  new = True
  for d in visitor:
    if operator.eq(d, c):
      new = False
      break
  if new == True:
    visitor.append(c)
    if (len(visitor) > 100):
      visitor.pop(0)
    update_db_read_cnt({'uuid':uuid, 'read_cnt':p['read_cnt']+1})

  return render_template('blog/blog.html', post=pp)

def get_post(uuid, check_author=True):
    post = get_db().execute(
        'SELECT p.uuid, title, body, created, updated, author_id, username, read_cnt, good_cnt, tags, tags_index'
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
    tags = request.form['tags']
    tags_index = request.form['tags_index']
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
                 'tags_index':tags_index,
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
        tags = request.form['tags']
        tags_index = request.form['tags_index']

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
                     'tags_index':tags_index,
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

