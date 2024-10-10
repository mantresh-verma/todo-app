from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base



                        # 'mysql+pymysql://your_username:your_password@localhost/your_database_name'
# SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:root@127.0.0.1:3306/TodoAppDatabase' 

SQLALCHEMY_DATABASE_URL = 'sqlite:///./todosapp.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()