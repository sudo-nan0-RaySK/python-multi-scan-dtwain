from . import constants
from .exceptions import *
import ctypes
import os
lib = os.path.join(os.path.dirname(__file__), "bin", "dtwain32u.dll")
mydll = ctypes.windll.LoadLibrary(lib)

def arrayToList(array):
	if not mydll.DTWAIN_IsInitialized():
		raise notInitializedException("dtwain has not initialized yet.")
	values = []
	count=mydll.DTWAIN_ArrayGetCount(array)
	type = mydll.DTWAIN_ArrayGetType(array)
	for 	i in range(count):
		if type == constants.DTWAIN_ARRAYFLOAT:
			value = ctypes.c_double()
		if type in (constants.DTWAIN_ARRAYFRAME, constants.DTWAIN_ARRAYHANDLE, constants.DTWAIN_ARRAYINT16, constants.DTWAIN_ARRAYINT32, constants.DTWAIN_ARRAYSOURCE):
			value = ctypes.c_int()
		if type == constants.DTWAIN_ARRAYLONG:
			value = ctypes.c_long()
		if type in (constants.DTWAIN_ARRAYUINT16, constants.DTWAIN_ARRAYUINT32):
			value = ctypes.c_uint()
		if type == constants.DTWAIN_ARRAYSTRING:
			length = mydll.DTWAIN_ArrayGetStringLength(array, i)
			bytesCount = length*4+10
			value = ctypes.create_unicode_buffer("\0" * bytesCount)
		mydll.DTWAIN_ArrayGetAt(array, i, ctypes.byref(value))
		if type in (constants.DTWAIN_ARRAYSTRING, constants.DTWAIN_ARRAYUINT16, constants.DTWAIN_ARRAYUINT32, constants.DTWAIN_ARRAYLONG, constants.DTWAIN_ARRAYINT16, constants.DTWAIN_ARRAYINT32, constants.DTWAIN_ARRAYFLOAT):
			values.append(value.value)
		else:
			values.append(value)
	return values

def getNameFromCap(cap):
	if not mydll.DTWAIN_IsInitialized():
		raise notInitializedException("dtwain has not initialized yet.")
	name = ctypes.create_unicode_buffer("\0" * 1024)
	mydll.DTWAIN_GetNameFromCapW(cap, ctypes.byref(name), 1024)
	return name.value

def getSourceStringList():
	try:
		d = dtwain()
	except twainNotFoundError:
		return []
	sources = d.source_string_list
	d.close()
	return sources

def raiseErrorException():
	if not mydll.DTWAIN_IsInitialized():return
	errorCode = mydll.DTWAIN_GetLastError()
	if errorCode == 0: return
	strBuffer = ctypes.create_unicode_buffer("\0"*324)
	errorStrLen = mydll.DTWAIN_GetErrorStringW(errorCode, ctypes.byref(strBuffer), 255)
	raise dtwainException(strBuffer.value)


class dtwain:
	def __init__(self, debug = True):
		if not mydll.DTWAIN_IsTwainAvailable():
			raise twainNotFoundError("this computer has not installed twain device.")
		if not mydll.DTWAIN_IsInitialized():
			mydll.DTWAIN_SysInitialize()
		if debug:
			mydll.DTWAIN_SetTwainLog(constants.DTWAIN_LOG_USEFILE|constants.DTWAIN_LOG_CALLSTACK|constants.DTWAIN_LOG_ERRORMSGBOX, "twain.log")
		self.sourceArray = ctypes.c_int()
		mydll.DTWAIN_EnumSources(ctypes.byref(self.sourceArray))

	@property
	def source_list(self):
		sources = arrayToList(self.sourceArray)
		return sources

	@property
	def source_string_list(self):
		stringList = []
		for source in self.source_list:
			name = ctypes.create_unicode_buffer('\0' * 64)
			mydll.DTWAIN_GetSourceProductName(source, ctypes.byref(name), 128)
			stringList.append(name.value)
		return stringList

	def getProductName(self, source):
		name = ctypes.create_unicode_buffer('\0' * 64)
		mydll.DTWAIN_GetSourceProductName(source, ctypes.byref(name), 128)
		return name.value

	def getSource(self, source):
		return dtwain_source(source)

	def selectSource(self):
		source = mydll.DTWAIN_SelectSource()
		if source == 0:
			return False
		return dtwain_source(source)

	def getSourceByName(self, name):
		source = mydll.DTWAIN_SelectSourceByName(name)
		if source == 0:
			status = mydll.DTWAIN_GetLastError()
			raise sourceOpenException("source open failed error code is %d" % (status))
		return dtwain_source(source)


	def close(self):
		mydll.DTWAIN_ArrayDestroy(self.sourceArray)
		mydll.DTWAIN_SysDestroy()

	def __del__(self):
		self.close()

class dtwain_source:
	def __init__(self, source):
		self.status = 0
		ret = mydll.DTWAIN_OpenSource(source)
		if not ret:
			status = mydll.DTWAIN_GetLastError()
			raise sourceOpenException("source open failed error code is %d" % (status))
		self.source = source

	def isSourceOpen(self):
		ret = mydll.DTWAIN_IsSourceOpen(self.source)
		return bool(ret)

	def isDeviceOnline(self):
		online = mydll.DTWAIN_IsDeviceOnline(self.source)
		return bool(online)

	def raiseDeviceOffline(self):
		if not self.isDeviceOnline():
			raise sourceOfflineException("the scanner is offline.")

	def getResolution(self):
		res = ctypes.c_double()
		mydll.DTWAIN_GetResolution(self.source, ctypes.byref(res))
		return res.value

	def setResolution(self, resolution):
		ret = mydll.DTWAIN_SetResolution(self.source, ctypes.c_double(resolution))
		if not ret:
			raiseErrorException()
		return

	def isDuplexSupported(self):
		ret = mydll.DTWAIN_IsDuplexSupported(self.source)
		raiseErrorException()
		return bool(ret)

	def enableDuplex(self, enable = True):
		if not mydll.DTWAIN_IsDuplexSupported(self.source):
			return False
		ret = mydll.DTWAIN_EnableDuplex(self.source, enable)
		if not ret:
			#raiseErrorException()
			pass
		return True

	def isAcquiring(self):
		ret = mydll.DTWAIN_IsSourceAcquiring(self.source)
		return bool(ret)

	def enumSupportedCaps(self):
		array = ctypes.c_int()
		ret = mydll.DTWAIN_EnumSupportedCaps(self.source, ctypes.byref(array))
		if not ret:
			return mydll.DTWAIN_GetLastError()
		caps = arrayToList(array)
		mydll.DTWAIN_ArrayDestroy(array)
		return caps

	def isDuplexEnabled(self):
		ret = mydll.DTWAIN_IsDuplexEnabled(self.source)
		return bool(ret)

	def isFeederEnabled(self):
		if not self.isFeederSupported():
			return False
		ret = self.getCapValue(constants.CAP_FEEDERENABLED, constants.DTWAIN_CAPGETCURRENT)[0]
		return bool(ret)

	def isFeederSupported(self):
		ret = self.isCapSupported(constants.CAP_FEEDERENABLED)
		return bool(ret)

	def isFeederLoaded(self):
		if not self.isFeederEnabled():
			return False
		ret = mydll.DTWAIN_IsFeederLoaded(self.source)
		return bool(ret)

	def acquireFile(self, fileNameList, fileType, fileCtrlFlag = constants.DTWAIN_USELONGNAME, pixelType = constants.DTWAIN_PT_RGB, bShowUi = False):
		page = 1
		if self.isDuplexEnabled():
			page = 2
		nameArray = mydll.DTWAIN_ArrayCreate(constants.DTWAIN_ARRAYSTRING, page)
		for i in range(page):
			mydll.DTWAIN_ArraySetAtString(nameArray, i, fileNameList[i])
		self.status = ctypes.c_int()
		mydll.DTWAIN_AcquireFileEx(self.source, nameArray, fileType, fileCtrlFlag, pixelType, page, bShowUi, True, ctypes.byref(self.status))
		mydll.DTWAIN_ArrayDestroy(nameArray)

	def acquire_and_write_file(self, fileName, fileType, fileCtrlFlag = constants.DTWAIN_USELONGNAME, pixelType = constants.DTWAIN_PT_RGB, bShowUi = False):
		self.status = ctypes.c_int()
		b_str_fileName = str(fileName).encode('utf-8')
		mydll.DTWAIN_AcquireFileA(self.source, ctypes.c_char_p(b_str_fileName), fileType, fileCtrlFlag, pixelType, True, bShowUi, True, ctypes.byref(self.status))

	def getNeedPageCount(self):
		page = 1
		if self.isDuplexEnabled():
			page = 2
		return page

	def setBlankPageDetection(self, threshold, options = constants.DTWAIN_BP_AUTODISCARD_ANY, enable = True):
		ret = mydll.DTWAIN_SetBlankPageDetection(self.source, ctypes.c_double(threshold), ctypes.c_long(options), enable)
		return ret

	def isCapSupported(self, cap):
		supported = mydll.DTWAIN_IsCapSupported(self.source, cap)
		return bool(supported)

	def getCapValue(self, cap, mode = constants.DTWAIN_CAPGETCURRENT):
		values = []
		array = ctypes.c_int()
		ret = mydll.DTWAIN_GetCapValues(self.source, cap, mode, ctypes.byref(array))
		if not ret:
			return mydll.DTWAIN_GetLastError()
		values = arrayToList(array)
		mydll.DTWAIN_ArrayDestroy(array)
		if mode == constants.DTWAIN_CAPGETCURRENT or mode == constants.DTWAIN_CAPGETDEFAULT:
			if len(values) == 0:
				return
		return values

	def getLastError(self):
		ret = mydll.DTWAIN_GetLastError()
		return ret

	def close(self):
		if mydll.DTWAIN_IsInitialized():
			ret = mydll.DTWAIN_CloseSource(self.source)
			if not ret:
				raise dtwainException("source close failed")

	def __del__(self):
		self.close()
