from dbfpy3 import dbf as dbf2

dbfh = dbf2.DbfHeader()
dbfh.add_field(('nam', "C", 10))