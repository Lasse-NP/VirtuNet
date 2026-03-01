from GUI import frontpage
import logging

def fetchdependencies():
    logging.info('No Dependencies Fetched')
    # System Dependencies to fetch: MiniNet, OpenvSwitch, OpenVPN

if __name__ == '__main__':
    fetchdependencies()
    frontpage.startgui()