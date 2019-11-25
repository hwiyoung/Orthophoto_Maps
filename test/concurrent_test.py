# https://dzone.com/articles/python-how-to-tell-if-a-function-has-been-called
import functools
import socket

def calltracker(func):
    @functools.wraps(func)
    def wrapper(*args):
        wrapper.has_been_called = True
        return func(*args)
    wrapper.has_been_called = False
    return wrapper

@calltracker
def doubler(number):
    check = 0
    while check < 500000000:
        check += 1
    print(check)

# @calltracker
# def doubler(number):
#     print(number*2)

if __name__ == '__main__':
    while True:
        ################################
        # Server for path, frame, bbox #
        ################################
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 57810))
        print("binding...")

        data, addr = s.recvfrom(200)

        header = data[:5]
        if header == b'START':
            # doubler(2)  # if a function is called... print('doubler has been called!')
            # if a function is NOT called... print("You haven't called this function yet")
            if not doubler.has_been_called:
                print("You haven't called this function yet")
                doubler(2)
                doubler.has_been_called = False
            if doubler.has_been_called:
                print('doubler has been called!')
