
class dtwainException(Exception):pass

class notInitializedException(dtwainException):pass

class twainNotFoundError(dtwainException):pass

class sourceException(Exception):pass

class sourceOpenException(sourceException): pass

class sourceOfflineException(sourceException):pass

class invalidSourceException(sourceException):pass