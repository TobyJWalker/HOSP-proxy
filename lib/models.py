import peewee
import datetime

# connect to the database file
db = peewee.SqliteDatabase('database.sqlite')

# create authorisation table based on Peewee Model
class Authorisation(peewee.Model):
    # create fields
    header = peewee.CharField()
    date_added = peewee.DateTimeField(default=datetime.datetime.now) # default is timestamp added

    class Meta: # some database metadata
        database = db
        table_name = 'authorisation'

# function to create tables
def create_tables():
    db.create_tables([Authorisation], safe=True)