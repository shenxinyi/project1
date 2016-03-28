#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from flask import session


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)

#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@w4111db.eastus.cloudapp.azure.com/username
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db.eastus.cloudapp.azure.com/ewu2493"
#
DATABASEURI = "postgresql://yy2632:FSHKVY@w4111db.eastus.cloudapp.azure.com/yy2632"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args
  # print session['username']
  

  msg = 'Hello, everyone!'
  label = 'Login'
  if 'user' in session:
    msg = 'Welcome back, %s.' % session['user']
    label = 'Logout'

  context = dict(data = msg, data2 = label)

  #
  # example of a database query
  #

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/newuser')
def newuser():
  return render_template("newuser.html")

@app.route('/add', methods=['POST'])
def add():
  username=request.form['name']
  password=request.form['password']
  email=request.form['email']
  role = request.form.getlist('role')
  
  cursor = g.conn.execute("SELECT username FROM users")
  i=0
  for result in cursor:
    if username==result['username']:
      i=1
      break
  cursor.close()


  if i==0:
    # session['username']=request.form['name']
    g.conn.execute("INSERT INTO users (username,password,email) VALUES ('%s','%s','%s');" %(username,password,email))
    cursor = g.conn.execute("SELECT uid FROM users WHERE username = '%s';" % username)
    uid = []
    for result in cursor:
      uid.append(result[0])
    cursor.close()
    if 'buyer' in role:
      g.conn.execute("INSERT INTO buyer (uid) VALUES ('%s');" % uid[0])
    if 'seller' in role:
      g.conn.execute("INSERT INTO seller (uid) VALUES ('%s');" % uid[0])      
    return redirect('/')
  
  else:
    return redirect('/newuser')

# @app.route('/another')
# def another():
#   return render_template("anotherfile.html")

@app.route('/returnuser')
def returnuser():
  g.conn.execute("delete from shopcart;")
  if 'user' in session:
    
    session.pop('user', None)
    if 'bid' in session:
      g.conn.execute("delete from shopcart where bid='%s';" %session['bid'])
      session.pop('buyer', None)
    if 'sid' in session:
      session.pop('seller', None)
    return redirect('/')
  else:
    return render_template("returnuser.html")

@app.route('/login', methods=['POST'])
def login():
  username=request.form['username']
  password=request.form['password']
  print username
  cursor = g.conn.execute("SELECT username,password FROM users")
  i=0
  for result in cursor:
    print password
    if username==result['username'] and password==result['password']:
      i=1
      break
  cursor.close()
  if i==1:
    session['user'] = username
    cursor = g.conn.execute("SELECT U.username, B.bid FROM buyer B, users U WHERE B.uid=U.uid;")
    for result in cursor:
      if session['user']==result['username']:
        session['bid'] = result['bid']
    cursor.close()
    cursor = g.conn.execute("SELECT U.username, S.sid FROM seller S, users U WHERE S.uid=U.uid;")
    for result in cursor:
      if session['user']==result['username']:
        session['sid'] = result['sid']
    cursor.close()
    print session ['user']
    return redirect('/')
  else:
    return redirect('/returnuser')

@app.route('/post')
def post():
  if 'sid' in session:
        return render_template("post.html")
  return render_template("notseller.html")

@app.route('/addproduct', methods=['POST'])
def addproduct():
  pname=request.form['productname']
  price=request.form['price']
  condition=request.form['condition']
  cursor=g.conn.execute("SELECT s.sid FROM users u,seller s WHERE u.username='%s' AND u.uid=s.uid;" %session['user'])
  # sidresult=g.conn.execute("SELECT s.sid FROM users u,sellers s WHERE u.username='%s' AND u.uid=s.uid;", % session['user'])
  sid=[]
  for result in cursor:
    sid.append(result[0])
  cursor.close()
  print sid[0]
  # g.conn.execute("INSERT INTO seller (uid) VALUES ('%s');" % uid[0])
  g.conn.execute("INSERT INTO product_sells (sid,pname,price,condition) VALUES ('%s','%s','%s','%s');" %(sid[0],pname,price,condition))
  return redirect('/')

@app.route('/seeproduct')
def seeproduct():
  if 'bid' not in session:
    return render_template("notbuyer.html")
  cursor = g.conn.execute("SELECT * FROM product_sells where condition !='sold';")
  product = []
  for result in cursor:
    one = []
    one.append(result['pid'])
    one.append(str(result['pname']))
    one.append(result['price'])
    one.append(str(result['condition']))
    product.append(one)
  cursor.close()
  context = dict(data=product)
  return render_template("seeproduct.html", **context)

@app.route('/addtocart', methods=['POST'])
def addtocart():
  pid=request.form['pid']
  g.conn.execute("INSERT INTO shopcart (pid,bid) VALUES ('%s','%s');" %(pid, session['bid']))
  return redirect('/seeproduct')
 
@app.route('/gotocart')
def gotocart():
  print session['bid']
  cursor = g.conn.execute("SELECT p.pid, p.pname, p.price, p.condition FROM product_sells p,shopcart s WHERE s.pid=p.pid AND s.bid='%s';" %session['bid'])
  product=[]
  for result in cursor:
    one=[]
    one.append(result['pid'])
    one.append(str(result['pname']))
    one.append(result['price'])
    one.append(str(result['condition']))
    product.append(one)
  cursor.close()
  context = dict(data=product)
  return render_template("cart.html", **context)  # cursor.close()

@app.route('/gotopay')
def gotopay():
  cursor=g.conn.execute("SELECT s.bid,count(*) AS amount, sum(p.price) AS total_price FROM shopcart s, product_sells p WHERE s.pid=p.pid GROUP BY s.bid")
  order=[]
  for result in cursor:
    # one=[]
    # one.append(result['amount'])
    # one.append(result['total_price'])
    g.conn.execute("INSERT INTO orders (amount,total_price) VALUES(%s,%s);" %(result['amount'],result['total_price']))
    # order.append(one)
  cursor.close()

  cursor = g.conn.execute("SELECT oid,amount,total_price from orders;")
  oid = []
  amount = []
  total_price = []
  for result in cursor:
    oid.append(result['oid'])
    amount.append(result['amount'])
    total_price.append(result['total_price'])
  cursor.close()

  cursor=g.conn.execute("SELECT bid,pid FROM shopcart WHERE bid='%s';" %session['bid'])
  for result in cursor:
    print result['pid']
    g.conn.execute("INSERT INTO order_create (oid,bid,pid) VALUES('%s','%s','%s');" %(oid[-1],session['bid'],result['pid']))
    g.conn.execute("UPDATE product_sells SET condition='sold' WHERE pid='%s';" %result['pid'])
  cursor.close()

  cursor = g.conn.execute("SELECT p.pid, p.pname, p.price, p.condition FROM product_sells p,shopcart s WHERE s.pid=p.pid AND s.bid='%s';" %session['bid'])
  product=[]
  for result in cursor:
    one=[]
    one.append(result['pid'])
    one.append(str(result['pname']))
    one.append(result['price'])
    one.append(str(result['condition']))
    product.append(one)
  cursor.close()
  context = dict(data=product,data2=oid[-1],data3=amount[-1],data4=total_price[-1])

  g.conn.execute("DELETE FROM shopcart;")
  return render_template("paysuccess.html", **context)
  
@app.route('/myproducts')
def myproducts():
  if 'bid' not in session:
    return render_template("notbuyer.html")
  cursor = g.conn.execute("SELECT p.pid, p.pname FROM order_create o, product_sells p where o.pid=p.pid AND o.bid='%s';" %session['bid'])
  product = []
  for result in cursor:
    one = []
    one.append(result['pid'])
    one.append(str(result['pname']))
    product.append(one)
  cursor.close()
  context = dict(data=product)
  return render_template("myproducts.html", **context)

@app.route('/feedback', methods=['POST'])
def feedback():
  pid=request.form['pid']
  # cursor = g.conn.execute("SELECT pid FROM feedback_given;")
  # i=0
  # for result in cursor:
  #   intpid=int(result['pid'])
  #   print intpid
  #   print pid
  #   print pid==intpid
  #   if pid==intpid:
  #     i=1
  #     print i
  #     break
  # cursor.close()
  # if i==1:
  #   return redirect('/myproducts')
  accuracy=request.form['accuracy']
  g.conn.execute("INSERT INTO feedback_given (pid,bid,accuracy) VALUES ('%s','%s', '%s');" %(pid, session['bid'], accuracy))
  return redirect('/')

# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
#   return redirect('/')


# @app.route('/login')
# def login():
#     abort(401)
#     this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
