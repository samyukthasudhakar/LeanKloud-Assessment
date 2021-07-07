from flask import Flask, request
from flask_restplus import Api, Resource, fields, reqparse
from werkzeug.contrib.fixers import ProxyFix
from datetime import datetime, date
from functools import wraps
import mysql.connector as db

app = Flask(__name__)

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}


app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app,version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',authorizations=authorizations
)

valid_tokens = ["read","write"]

# decorator function to enable read access 
def read_token(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None
        
        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']

        if not token:
            api.abort(404,'Token is missing')

        if token not in valid_tokens:
            api.abort(403,'Invalid Token')

        return f(*args, **kwargs)
    return decorated

# decorator function to enable write access
def write_token(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        token = None
        
        if 'X-API-KEY' in request.headers:
            token = request.headers['X-API-KEY']

        if not token:
            api.abort(404,'Token is missing')

        if token not in valid_tokens:
            api.abort(403,'Invalid Token')

        if token!="write":
            api.abort(403,'Access Denied')

        return f(*args, **kwargs)
    return decorated

# declaring the namespaces
ns = api.namespace('todos', description='TODO operations')
dueby_ns= api.namespace('due',description="Task's that are due to be finished on a specific date")
overdue_ns = api.namespace('overdue',description="Task's that are overdue")
finished_ns = api.namespace('finished',description="Task's that are finished")


todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'dueby': fields.Date(required=True, description='The date by when this task should be finished'),
    'status': fields.String(required=True, description='Notifies the status of the task : NOT STARTED/IN PROGRESS/FINISHED') 
})

status = api.model('Status',{'status':fields.String(required=True,description='Notifies the status of the task : NOT STARTED/IN PROGRESS/FINISHED')})

# database connection and cursor creation
mydb = db.connect(host="localhost", user="root", password="root@123", database="todos")
cursor = mydb.cursor(buffered=True)

class TodoDAO(object):

    def convert(self,task):
        formatted_Task = {"id":task[0],"task":task[1],"dueby":task[2],"status":task[3]}
        return(formatted_Task)

    def validate_status(self,status):
        if status not in ["NOT STARTED","IN PROGRESS","FINISHED"]:
            return("Please make sure status value is one among the following - 'NOT STARTED','IN PROGRESS','FINISHED' ")
        else:
            return True

    def validate_date(self,date):
        try:
            if date != datetime.strptime(date, "%Y-%m-%d").strftime('%Y-%m-%d'):
                raise ValueError
            return True
        except ValueError:
            return("Please make sure the date value for dueby is of the format : YYYY-MM-DD")

    # to fetch all the todos present in the database
    def getAll(self):
        cursor.execute("SELECT * FROM tasks")
        rows=cursor.fetchall()

        tasks=[]

        for task in rows:
            tasks.append(self.convert(task))
        
        return tasks

    # to get a todo with the specific id value
    def get(self,id):
        try:
            cursor.execute("SELECT * FROM tasks WHERE id={}".format(id))
            task=cursor.fetchone()
            task=self.convert(task)
            return task
        except:
            api.abort(404,"Todo {} doesn't exist".format(id))
    
    # to create a new todo
    def create(self, data):
        params=(data["task"],data["dueby"],data["status"])

        status_validation = self.validate_status(data["status"])
        if status_validation!=True:
            api.abort(400,status_validation)

        dueby_validation = self.validate_date(data["dueby"])
        if dueby_validation!=True:
            api.abort(400,dueby_validation)
            
        cursor.execute("INSERT INTO tasks(task,dueby,status) VALUES(%s, %s, %s)",params)
        mydb.commit()

        cursor.execute("SELECT * FROM tasks where id=(SELECT MAX(id)from tasks)")
        task=cursor.fetchone()
        task=self.convert(task)
        
        return task

    # to update an existing todo
    def update(self, id, data):
        params = (data["task"],data["dueby"],data["status"],id)

        cursor.execute("SELECT * FROM tasks where id={}".format(id))
        row_count = cursor.rowcount

        if row_count == 0:
            api.abort(404,"Task with id {} doesn't exist".format(id))
        else:
            status_validation = self.validate_status(data["status"])
            if status_validation!=True:
                api.abort(400,status_validation)

            dueby_validation = self.validate_date(data["dueby"])
            if dueby_validation!=True:
                api.abort(400,dueby_validation)
                
            cursor.execute("UPDATE tasks SET task=(%s),dueby=(%s),status=(%s) WHERE id=(%s)",params)
            mydb.commit()

        cursor.execute("SELECT * FROM tasks where id={}".format(id))
        task=cursor.fetchone()
        task=self.convert(task)

        return task

    # to delete a todo given it's id
    def delete(self, id):
        cursor.execute("SELECT * FROM tasks where id={}".format(id))
        row_count = cursor.rowcount
        if row_count == 0:
            api.abort(404,"Task with id {} doesn't exist".format(id))
        else:   
            cursor.execute("DELETE FROM tasks WHERE id = {}".format(id))
            mydb.commit()
        return(204,{'message':'Todo Deleted'})

    # to update the status field of a todo item
    def update_status(self,id,new_status):
        params = (new_status["status"],id)

        cursor.execute("SELECT * FROM tasks where id={}".format(id))
        row_count = cursor.rowcount
        if row_count == 0:
            api.abort(404,"Task with id {} doesn't exist".format(id))
        
        status_validation = self.validate_status(params[0])
        if status_validation!=True:
            api.abort(400,status_validation)
            
        cursor.execute("UPDATE tasks SET status=(%s) where id=(%s)",params)

        return new_status
    
    # to fetch all the todos that are dueby a given date
    def dueby(self,date):
        dueby_validation = self.validate_date(date)
        if dueby_validation!=True:
            api.abort(400,dueby_validation)
            
        cursor.execute('SELECT * FROM tasks WHERE date(dueby)="{}"'.format(date))
        rows=cursor.fetchall()
        tasks=[]

        for task in rows:
            tasks.append({"id":task[0],"task":task[1],"dueby":str(task[2]),"status":task[3]})
        
        return tasks

    # to fetch todos that are overdue in comparison to the current date
    def overdue(self):
        today=date.today()
        cur_date = today.strftime('%Y-%m-%d')

        cursor.execute('SELECT * FROM tasks WHERE date(dueby)<="{}" AND status!="FINISHED"'.format(cur_date))

        rows=cursor.fetchall()
        tasks=[]

        for task in rows:
            tasks.append(self.convert(task))

        return tasks

    # to fetch todos that are finished
    def finished(self):
        cursor.execute('SELECT * FROM tasks WHERE status="FINISHED"')
        tasks=cursor.fetchall()

        result = []
        for task in tasks:
            result.append(self.convert(task))

        if len(result)==0:
            api.abort(404,"Zero finished tasks")
        else:
            return result

DAO=TodoDAO()


@ns.route('/')
@ns.response(403,'Invalid Token')
@ns.response(404,'Not Found')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    @ns.doc(security='apikey')
    @read_token
    def get(self):
        '''List all tasks'''
        return DAO.getAll()
    
    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo)
    @ns.response(201, 'Todo created')
    @ns.doc(security='apikey')
    @write_token
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload),201


@ns.route('/<int:id>')
@ns.response(403,'Invalid Token')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):

    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    @ns.doc(security='apikey')
    @read_token
    def get(self, id):
        '''Fetch a given resource'''
        return DAO.get(id)
    
    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    @ns.doc(security='apikey')
    @write_token
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    @ns.doc(security='apikey')
    @write_token
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)

    @ns.expect(status)
    @ns.doc(security='apikey')
    @ns.marshal_with(status,code=204)
    @write_token
    def patch(self,id):
        '''Update the status of a task'''
        return DAO.update_status(id, api.payload)


due_params = reqparse.RequestParser()
due_params.add_argument('due_date',type=str,required=True)

@dueby_ns.route('')
class Due(Resource):
    @dueby_ns.expect(due_params,validate='True')
    @dueby_ns.marshal_with(todo)
    @dueby_ns.response(403,'Invalid Token')
    @dueby_ns.response(404,'No todos due by given date')
    @dueby_ns.doc(security='apikey')
    @read_token
    def get(self):
        '''Fetch todos that are dueby inputed date'''
        date = request.args.get('due_date')
        return DAO.dueby(date)
        

@overdue_ns.route('/')
class OverDue(Resource):
    @overdue_ns.marshal_with(todo)
    @overdue_ns.response(403,'Invalid Token')
    @overdue_ns.response(404,'No todos are overdue')
    @overdue_ns.doc(security='apikey')
    @read_token
    def get(self):
        return DAO.overdue()
    

@finished_ns.route('/')
class Finished(Resource):
    @finished_ns.marshal_with(todo)
    @finished_ns.response(403,'Invalid Token')
    @finished_ns.response(404, 'No finished todos')
    @finished_ns.doc(security='apikey')
    @read_token
    def get(self):
        return DAO.finished()


if __name__ == '__main__':
    app.run(debug=True)
