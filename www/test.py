def fun1():
    global __pool
    __pool = 1
    print(__name__, ': ', __pool)

def add():
    global __pool
    __pool += 1
    print(__name__, ': ', __pool)

def fun2():
    global __pool
    print(__name__, ': ', __pool)

if __name__ == '__main__':
    fun1()
    fun2()
    add()
    fun2()