import re
import sys
import os
import sqlite3

pattern = re.compile('^[A-Z1-9]{4}-[A-Z1-9]{3}$') # for code

def crash(mess):
    print(mess); close_db(); sys.exit()

def open_db(db): # statics conn and curs are preserved until calling function/program returns/exits
    if not os.path.isfile(db): crash('no db')
    open_db.conn = sqlite3.connect(db)
    open_db.curs = open_db.conn.cursor()
    print('existing db opened')

def close_db():
    open_db.curs.close()
    open_db.conn.close()
    print('db closed')

def commit():
    open_db.conn.commit()

def exec_ret(command, tup): # returns [] if no result, otherwise list of tuples
    return(open_db.curs.execute(command, tup).fetchall())

def exec(command, tup):
    try: open_db.curs.execute(command, tup)
    except Exception as e:
        print(e)
        return(False)
    return(True)

def is_code(code):
    return(len(exec_ret('select code from tree where code = ?', (code,))) >= 1)

def delete_tree(code):
    return(exec('delete from tree where code=?', (code,)))

def update_tree(old, new):
    return(exec('update tree set code=? where code=?', (new, old)))

def update_chains(old, new):
    return(exec('update chains set code=? where code=?', (new, old)))

def get_name(code):
    res = exec_ret('select name from tree where code = ?', (code,))
    res = [r[0] for r in res]
    if len(res) == 0: return ''
    return res[0]

def get_chains(code):
    res = exec_ret('select chain from chains where code = ?', (code,))
    return(', '.join([r[0] for r in res]))

def main():
    print('Program to replace and old ancestor with a new one.')
    open_db('tree.db')
    old = input('Enter the code of the old ancestor: ')
    if not bool(pattern.match(old)): crash('bad code: ' + old)
    if not is_code(old): crash('code not found: ' + old)
    print('Old ancestor name: ' + get_name(old))
    print('Old ancestor chains: ' + get_chains(old))
    new = input('Enter the code of the new ancestor: ')
    if not bool(pattern.match(new)): crash('bad code: ' + new)
    print('New ancestor name: ' + get_name(new))
    print('New ancestor chains: ' + get_chains(new))
    if is_code(new):
        print('New ancestor already exits: ' + new)
        input('Hit enter to delete old tree record')
        print('deleting old ancestor from tree...')
        if not delete_tree(old): crash('failed to delete from tree: ' + old)
    else:
        print('updating tree...')
        if not update_tree(old, new): crash('failed to update tree: ' + old)
    print('updating old chains...')
    if not update_chains(old, new): crash('failed update chains: ' + old)
    commit()
    print('Old ancestor name: ' + get_name(old))
    print('Old ancestor chains: ' + get_chains(old))
    print('New ancestor name: ' + get_name(new))
    print('New ancestor chains: ' + get_chains(new))

main()
