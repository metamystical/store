import pyautogui as pg
import math
import re
import time
import sys
import os
import sqlite3

def open_db(db): # statics conn and curs are preserved until calling function/program returns/exits
    is_db = False
    if os.path.isfile(db): is_db = True
    open_db.conn = sqlite3.connect('tree.db')
    open_db.curs = open_db.conn.cursor()
    if is_db: print('existing db opened')
    else:
        open_db.curs.execute('create table tree (id integer primary key autoincrement, code varchar(8) not null, name text, birth_date text, birth_place text, death_date text, death_place text)')
        open_db.curs.execute('create table chains (chain text not null unique, code varchar(8) not null)')
        print('new db created')
    return(is_db)

def exec_ret(command, tup): # returns [] if no result, otherwise list of tuples
    return(open_db.curs.execute(command, tup).fetchall())

def exec(command, tup):
    try: open_db.curs.execute(command, tup)
    except Exception as e:
        #print(e)
        return(False)
    return(True)

def is_code(code):
    return(len(exec_ret('select code from tree where code = ?', (code,))) >= 1)

def insert_tree(tup):
    exec('insert into tree (code, name, birth_date, birth_place, death_date, death_place) values (?, ?, ?, ?, ?, ?)', tup)

def insert_chains(tup):
    exec('insert into chains (chain, code) values (?, ?)', tup)

def detuple_list(tups):
    if tups == None: return([])
    return([tup[0] for tup in tups])

def get_code(chain): # returns code string or empty string if no code found
    res = exec_ret('select code from chains where chain = ?', (chain,))
    res = detuple_list(res)
    if len(res) == 0: return ''
    return res[0]

def get_chains(code): # returns list of chain strings
    res = exec_ret("select chain from chains where code = ?", (code,))
    return(detuple_list(res))

def get_gen(generation): # returns list of chain strings
    res = exec_ret('select distinct chain from chains where length(chain) = ? order by chain', (generation,))
    return(detuple_list(res))

def get_ccs_with_base(base): # returns list of tuples
    res = exec_ret("select chain, code from chains where chain like ?", (f'{base}%',))
    if res == None: return([])
    return(res)

def get_count(table):
    return(exec_ret(f'select count(*) from {table}', ())[0][0])

def commit():
    open_db.conn.commit()

def close_db():
    open_db.curs.close()
    open_db.conn.close()
    print('db closed')

def activate(title):
    found = False
    for window in pg.getAllWindows():
        if re.search('^' + title + '.*', window.title):
            found = True
            window.activate()
            time.sleep(2)
            break
    if not found:
        print('window not found:', title)
        sys.exit()

def setup():
    pg.click(1275, 303); time.sleep(1) # full screen
    pg.click(1247, 137); time.sleep(1) # center

# fan should be set to 7 generations and sized to maximum while still having all sectors clickable
# enter x,y screen coordinates of center (xc, yc), and lower left sectors going from ring 1 to ring ringmax - 1
# and separately ring ringmax - 1 lower right (xr, yr) below for calibration
def fan():
    coords = [(684, 535), (641, 502), (596, 526), (546, 545), (474, 576), (406, 608), (330, 640)]
    xc, yc = coords[0]
    xr, yr = (1034, 640) 
    ringmax = 7

    def radius_and_angle(tup):
        x, y = tup
        radius = math.sqrt((x - xc)**2 + (y - yc)**2)
        angle_rad = math.atan2(y - yc, x - xc)
        return radius, angle_rad

    rs = [0]
    for i in range(1, ringmax): rs.append(radius_and_angle(coords[i])[0])
    a_ll = radius_and_angle(coords[ringmax - 1])[1] # lower left outer ring sector angle
    da = (2 * math.pi - a_ll + radius_and_angle((xr, yr))[1]) / (2**(ringmax - 1) - 1)
    rings = []
    for ri in range(0, ringmax):
        ring = []
        factor = 2 ** (ringmax - 1 - ri)
        sa = a_ll + da * (factor - 1) / 2 
        for i in range(2**ri):
            a = sa + da * i * factor
            ring.append((int(xc + rs[ri] * math.cos(a)), int(yc + rs[ri] * math.sin(a))))
        rings.append(ring)
    sectors = ['']
    def permus(chain, length):
        if length == 0:
            sectors.append(chain)
            return
        permus(chain + 'F', length - 1)
        permus(chain + 'M', length - 1)
    for length in range(1, len(rings)): permus('', length)
    sec = 0
    for ri in range(0, len(rings)):
        for i in range(len(rings[ri])):
            sectors[sec] = (sectors[sec], ) + rings[ri][i]
            sec += 1
    return(sectors)
##        pg.moveTo(rings[ri][i][0], rings[ri][i][1])
##        time.sleep(1)
