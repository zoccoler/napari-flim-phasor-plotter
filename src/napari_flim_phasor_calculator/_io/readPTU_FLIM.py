''''
This package was copied from readPTU_FLIM library
(https://github.com/SumeetRohilla/readPTU_FLIM)

MIT License

Copyright (c) 2019 SumeetRohilla

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''


# Read PTU Library and FLIM data 
# Author: Sumeet Rohilla
# sumeetrohilla@gmail.com

# PTU Reader Library

"""
Created on Tue, 14 May 2019
Updated on Sun, 20 Dec, 2020
@author: SumeetRohilla, sumeetrohilla@gmail.com

"Good artists copy; great artists steal."

Largely inspired from examples:
- PicoQuant demo codes
  https://github.com/PicoQuant/PicoQuant-Time-Tagged-File-Format-Demos
- from a jupyter notebook by tritemio on GitHub:
  https://gist.github.com/tritemio/734347586bc999f39f9ffe0ac5ba0e66
    
Aim : Open and convert Picoquant .ptu image files for FLIM analysis
 *  Use : Simply select your .ptu file and library will provide:
 *  1) Lifetime image stack for each channel (1-8). 
 *     flim_data_stack  = [numPixX numPixY numDetectors numTCSPCbins]
 *     Fluorescence decays in each pixel/num_detection_channel are available for the whole acquisition
 *     Frame-wise info is not implemented here, but in principle is pretty straightforwad to implement
 *  2) Intensity is just acquisition flim_data_stack(in photons) is accessed by binning across axis  = numTCSPCbins and numDetectors
 *  3) get_flim_data_stack class method is numba accelarated (using @jit decorator) to gain speed in building flim_data_stack from raw_tttr_data 
 
"""

import time
import sys
import struct
import numpy as np
from numba import njit

@njit
def get_flim_data_stack_static(sync, tcspc, channel, special, header_variables):

    ImgHdr_Ident              = header_variables[0]
    MeasDesc_Resolution       = header_variables[1]
    MeasDesc_GlobalResolution = header_variables[2]
    ImgHdr_PixX               = header_variables[3]
    ImgHdr_PixY               = header_variables[4]
    ImgHdr_LineStart          = header_variables[5]
    ImgHdr_LineStop           = header_variables[6]
    ImgHdr_Frame              = header_variables[7]

    if (ImgHdr_Ident == 9) or (ImgHdr_Ident == 3):

        tcspc_bin_resolution = 1e9*MeasDesc_Resolution          # in Nanoseconds
        sync_rate            = np.ceil(MeasDesc_GlobalResolution*1e9)  # in Nanoseconds

#             num_of_detectors     = np.max(channel)+1
#             num_tcspc_channel    = np.max(tcspc)+1
#             num_tcspc_channel    = floor(sync_rate/tcspc_bin_resolution)+1

        num_of_detectors     = np.unique(channel).size 
        num_tcspc_channel    = np.unique(tcspc).size
        num_pixel_X          = ImgHdr_PixX
        num_pixel_Y          = ImgHdr_PixY


        flim_data_stack      = np.zeros((num_pixel_Y, num_pixel_X, num_of_detectors,num_tcspc_channel), dtype  = np.uint16)

        # Markers necessary to make FLIM image stack
        LineStartMarker = 2**(ImgHdr_LineStart-1)
        LineStopMarker  = 2**(ImgHdr_LineStop-1)
        FrameMarker     = 2**(ImgHdr_Frame-1)

        # Get Number of Frames
        FrameSyncVal    = sync[np.where(special == FrameMarker)]
        num_of_Frames   = FrameSyncVal.size
        read_data_range = np.where(sync == FrameSyncVal[num_of_Frames-1])[0][0]

        L1  = sync[np.where(special == LineStartMarker)] # Get Line start marker sync values
        L2  = sync[np.where(special == LineStopMarker)]  # Get Line start marker sync values

        syncPulsesPerLine = np.floor(np.mean(L2[10:] - L1[10:])) 

#             Get pixel dwell time values from header for PicoQuant_FLIMBee or Zeiss_LSM scanner

#             if 'StartedByRemoteInterface' in head.keys():

#                 #syncPulsesPerLine  = round((head.TimePerPixel/head.MeasDesc_GlobalResolution)*num_pixel_X);
#                 syncPulsesPerLine = np.floor(np.mean(L2[10:] - L1[10:])) 
#             else:  
#                 #syncPulsesPerLine  = floor(((head.ImgHdr_TimePerPixel*1e-3)/head.MeasDesc_GlobalResolution)*num_pixel_X);
#                 syncPulsesPerLine = np.floor(np.mean(L2[10:] - L1[10:]))


        # Initialize Variable
        currentLine        = 0
        currentSync        = 0
        syncStart          = 0
        currentPixel       = 0
        unNoticed_events   = 0
        countFrame         = 0
        insideLine         = False
        insideFrame        = False
        isPhoton           = False

        for event in range(read_data_range+1):

            if num_of_Frames == 1:
                # when only zero/one frame marker is present in TTTR file
                insideFrame = True

            currentSync    = sync[event]
            special_event  = special[event]

            # is the record a valid photon event or a special marker type event
            if special[event] == 0:
                isPhoton = True
            else:
                isPhoton = False

            if not(isPhoton):         
                #This is not needed once inside the first Frame marker
                if (special_event == FrameMarker):
                    insideFrame  = True
                    countFrame   += 1
                    currentLine  = 0

                if (special_event == LineStartMarker):

                    insideLine = True
                    syncStart  = currentSync

                elif (special_event == LineStopMarker):

                    insideLine   = False
                    currentLine  += 1
                    syncStart    = 0 

                    if (currentLine >= num_pixel_Y):
                        insideFrame  = False
                        currentLine  = 0

            # Build FLIM image data stack here for N-spectral/tcspc-input channels

            if (isPhoton and insideLine and insideFrame):

                currentPixel = int(np.floor((((currentSync - syncStart)/syncPulsesPerLine)*num_pixel_X)))
                tmpchan   = channel[event]
                tmptcspc  = tcspc[event]

                if (currentPixel < num_pixel_X) and (tmptcspc<num_tcspc_channel):
                    flim_data_stack[currentLine][currentPixel][tmpchan][tmptcspc] +=1
#         else:        
#             print("Piezo Scanner Data Reader Not Implemented Yet!!! \n")


    return flim_data_stack


class PTUreader():
    
    """
    PTUreader() provides the capability to retrieve raw_data or image_data from a PTU file acquired using available PQ TCSPC module in the year 2019
    
    Input arguements:
    
    filename= path + filename
    print_header  = True or False
    
    Output
    
    ptu_read_raw_data     = This function reads single-photon data from the file 'name'
                            The output variables contain the followig data:
                            sync       : number of the sync events that preceeded this detection event
                            tcspc      : number of the tcspc-bin of the event
                            channel    : number of the input channel of the event (detector-number)
                            special    : marker event-type (0: photon; else : virtual photon/line_Startmarker/line_Stopmarker/framer_marker)
                            
    For example: Please see Jupyter notebook for additional info on how to get raw TTTR data
                    
    get_flim_data_stack    = This function builds a FLIM image from raw tttr_data
                             Outputs: flim_data_stack  = [numPixX numPixY numDetectors numTCSPCbins]
    
    """
    
    # Global constants
    # Define different tag types in header
    
    tag_type = dict(
    tyEmpty8      = 0xFFFF0008,
    tyBool8       = 0x00000008,
    tyInt8        = 0x10000008,
    tyBitSet64    = 0x11000008,
    tyColor8      = 0x12000008,
    tyFloat8      = 0x20000008,
    tyTDateTime   = 0x21000008,
    tyFloat8Array = 0x2001FFFF,
    tyAnsiString  = 0x4001FFFF,
    tyWideString  = 0x4002FFFF,
    tyBinaryBlob  = 0xFFFFFFFF,
    )
    
    # Dictionary with Record Types format for different TCSPC devices and corresponding T2 or T3 TTTR mode
    rec_type = dict(
        rtPicoHarpT3     = 0x00010303,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $03 (PicoHarp)
        rtPicoHarpT2     = 0x00010203,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $02 (T2), HW: $03 (PicoHarp)
        rtHydraHarpT3    = 0x00010304,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $04 (HydraHarp)
        rtHydraHarpT2    = 0x00010204,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $02 (T2), HW: $04 (HydraHarp)
        rtHydraHarp2T3   = 0x01010304,  # (SubID = $01 ,RecFmt: $01) (V2), T-Mode: $03 (T3), HW: $04 (HydraHarp)
        rtHydraHarp2T2   = 0x01010204,  # (SubID = $01 ,RecFmt: $01) (V2), T-Mode: $02 (T2), HW: $04 (HydraHarp)
        rtTimeHarp260NT3 = 0x00010305,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $05 (TimeHarp260N)
        rtTimeHarp260NT2 = 0x00010205,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $02 (T2), HW: $05 (TimeHarp260N)
        rtTimeHarp260PT3 = 0x00010306,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $06 (TimeHarp260P)
        rtTimeHarp260PT2 = 0x00010206,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $02 (T2), HW: $06 (TimeHarp260P)
        rtMultiHarpNT3   = 0x00010307,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $03 (T3), HW: $07 (MultiHarp150N)
        rtMultiHarpNT2   = 0x00010207,  # (SubID = $00 ,RecFmt: $01) (V1), T-Mode: $02 (T2), HW: $07 (MultiHarp150N)
    )

    def __init__(self, filename, print_header_data = False):
        
        # raw_tttr_data = False, get_image_data = True
        # if get_image_data = True then get_raw_data = False
        # else get_raw_data = True and get_image_data = False
        # Usually a user will only demand for raw or image data
                
        #Reverse mappins of tag-type and record-type dictionary
        self.tag_type_r = {j: k for k, j in self.tag_type.items()}
        self.rec_type_r = {j: k for k, j in self.rec_type.items()}
        
        self.ptu_name        = filename
        self.print_header    = print_header_data
        
        f = open(self.ptu_name, 'rb')
        self.ptu_data_string = f.read() # ptu_data_string is a string of bytes and reads all file in memory
        f.close()

        
        #Check if the input file is a valid input file
        # Read magic and version of the PTU File
        self.magic = self.ptu_data_string[:8].rstrip(b'\0')
        self.version = self.ptu_data_string[8:16].rstrip(b'\0')
        if self.magic != b'PQTTTR':
            raise IOError("This file is not a valid PTU file. ")
            exit(0)
                

        
        self.head        = {}
        
        # Read  and print header if set True
        self._ptu_read_head(self.ptu_data_string)
        # Read and return Raw TTTR Data
        self._ptu_read_raw_data()
        
        if self.print_header == True:
            return self._print_ptu_head()
        
        return None
    
    def _ptu_TDateTime_to_time(self, TDateTime):

        EpochDiff = 25569  # days between 30/12/1899 and 01/01/1970
        SecsInDay = 86400  # number of seconds in a day

        return (TDateTime - EpochDiff) * SecsInDay

    
    def _ptu_read_tags(self, ptu_data_string, offset):

        # Get the header struct as a tuple
        # Struct fields: 32-char string, int32, uint32, int64

        tag_struct = struct.unpack('32s i I q', ptu_data_string[offset:offset+48])
        offset += 48

        # Get the tag name (first element of the tag_struct)
        tagName = tag_struct[0].rstrip(b'\0').decode()

        keys = ('idx', 'type', 'value')
        tag = {k: v for k, v in zip(keys, tag_struct[1:])}

        # Recover the name of the type from tag_dictionary
        tag['type'] = self.tag_type_r[tag['type']]
        tagStringR='NA'

        # Some tag types need conversion to appropriate data format
        if tag['type'] == 'tyFloat8':
            tag['value'] = np.int64(tag['value']).view('float64')
        elif tag['type'] == 'tyBool8':
            tag['value'] = bool(tag['value'])
        elif tag['type'] == 'tyTDateTime':
            TDateTime = np.uint64(tag['value']).view('float64')
            t = time.gmtime(self._ptu_TDateTime_to_time(TDateTime))
            tag['value'] = time.strftime("%Y-%m-%d %H:%M:%S", t)

        # Some tag types have additional data
        if tag['type'] == 'tyAnsiString':
            try: tag['data'] = ptu_data_string[offset: offset + tag['value']].rstrip(b'\0').decode()
            except: tag['data'] = ptu_data_string[offset: offset + tag['value']].rstrip(b'\0').decode(encoding  = 'utf-8', errors = 'ignore')
            tagStringR=tag['data']
            offset += tag['value']
        elif tag['type'] == 'tyFloat8Array':
            tag['data'] = np.frombuffer(ptu_data_string, dtype='float', count=tag['value']/8)
            offset += tag['value']
        elif tag['type'] == 'tyWideString':
            # WideString default encoding is UTF-16.
            tag['data'] = ptu_data_string[offset: offset + tag['value']*2].decode('utf16')
            tagStringR=tag['data']
            offset += tag['value']
        elif tag['type'] == 'tyBinaryBlob':
            tag['data'] = ptu_data_string[offset: offset + tag['value']]
            offset += tag['value']

        tagValue  = tag['value']

        return tagName, tagValue, offset, tagStringR
    
    
    def _ptu_read_head(self, ptu_data_string):
    
        offset         = 16
        FileTagEnd     = 'Header_End' 
        tag_end_offset = ptu_data_string.find(FileTagEnd.encode())

        tagName, tagValue, offset, tagString  = self._ptu_read_tags(ptu_data_string, offset)
        self.head[tagName] = tagValue

        #while offset < tag_end_offset:
        while tagName != FileTagEnd:
                tagName, tagValue, offset, tagString = self._ptu_read_tags(ptu_data_string, offset)
                if tagString=='NA': self.head[tagName] = tagValue
                else: self.head[tagName] = tagString
#                 print(tagName, tagValue)

        # End of Header file and beginning of TTTR data
        self.head[FileTagEnd] = offset


    def _print_ptu_head(self): 
        #print "head" dictionary     
        print("{:<30} {:8}".format('Head ID','Value'))

        for keys in self.head:
            val = self.head[keys] 
            print("{:<30} {:<8}".format(keys, val))     
    
    def _ptu_read_raw_data(self):
    
        '''
        This function reads single-photon data from the file 's'

        Returns:
        sync    : number of the sync events that preceeded this detection event
        tcspc   : number of the tcspc-bin of the event
        chan    : number of the input channel of the event (detector-number)
        special : indicator of the event-type (0: photon; else : virtual photon)
        num     : counter of the records that were actually read


        '''

        record_type = self.rec_type_r[self.head['TTResultFormat_TTTRRecType']]

        num_T3records = self.head['TTResult_NumberOfRecords']

        #Read all T3 records in memory
        t3records = np.frombuffer(self.ptu_data_string, dtype='uint32', count=num_T3records, offset= self.head['Header_End'])

        # Clear ptu string data from memory and delete it's existence
        del self.ptu_data_string

        #Next is to do T3Records formatting according to Record_type

        if record_type == 'rtPicoHarpT3':

            print('TCSPC Hardware: {}'.format(record_type[2:]))
            #   +----------------------+ T3 32 bit record  +---------------------+
            #   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x| --> 32 bit record
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | | | | | | | | | | | | | |  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  --> Sync
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | |x|x|x|x|x|x|x|x|x|x|x|x|  | | | | | | | | | | | | | | | | |  --> TCSPC bin
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   |x|x|x|x| | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Spectral/TCSPC input Channel
            #   +-------------------------------+  +-------------------------------+

            WRAPAROUND = 65536                                                   # After this sync counter will overflow
            sync       = np.bitwise_and(t3records, 65535)                        # Lowest 16 bits
            tcspc      = np.bitwise_and(np.right_shift(t3records, 16), 4095)     # Next 12 bits, dtime can be obtained from header
            chan       = np.bitwise_and(np.right_shift(t3records, 28),15)        # Next 4 bits 
            special    = ((chan==15)*1)*(np.bitwise_and(tcspc,15)*1)               # Last bit for special markers
            
            index      = ((chan==15)*1)*((np.bitwise_and(tcspc,15)==0)*1)        # Find overflow locations
            chan[chan==15]  = special[chan==15]
            chan[chan==1] = 0
            chan[chan==2] = 1
            chan[chan==4] = 0
            
        elif record_type == 'rtPicoHarpT2':

            print('TCSPC Hardware: {}'.format(record_type[2:]))

            #   +----------------------+ T2 32 bit record  +---------------------+
            #   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x| --> 32 bit record
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | |x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  --> Sync
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   |x|x|x|x| | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Spectral/TCSPC input Channel
            #   +-------------------------------+  +-------------------------------+

            WRAPAROUND = 210698240                                               # After this sync counter will overflow
            sync       = np.bitwise_and(t3records, 268435455)                    # Lowest 28 bits
            tcspc      = np.bitwise_and(t3records, 15)                           # Next 4 bits, dtime can be obtained from header
            chan       = np.bitwise_and(np.right_shift(t3records, 28),15)        # Next 4 bits 
            special    = ((chan==15)*1)*np.bitwise_and(tcspc,15)                 # Last bit for special markers
            index      = ((chan==15)*1)*((np.bitwise_and(tcspc,15)==0)*1)        # Find overflow locations

        elif record_type in ['rtHydraHarpT3', 'rtHydraHarp2T3', 'rtTimeHarp260NT3', 'rtTimeHarp260PT3','rtMultiHarpNT3']:

            print('TCSPC Hardware: {}'.format(record_type[2:]))

            #   +----------------------+ T3 32 bit record  +---------------------+
            #   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x| --> 32 bit record
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | | | | | | | | | | | | | |  | | | | | | |x|x|x|x|x|x|x|x|x|x|  --> Sync
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | | | | |x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x| | | | | | | | | | |  --> TCSPC bin
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | |x|x|x|x|x|x| | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Spectral/TCSPC input Channel
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   |x| | | | | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Special markers
            #   +-------------------------------+  +-------------------------------+
            WRAPAROUND = 1024                                                   # After this sync counter will overflow
            sync       = np.bitwise_and(t3records, 1023)                        # Lowest 10 bits
            tcspc      = np.bitwise_and(np.right_shift(t3records, 10), 32767)   # Next 15 bits, dtime can be obtained from header
            chan       = np.bitwise_and(np.right_shift(t3records, 25),63)       # Next 8 bits 
            special    = np.bitwise_and(t3records,2147483648)>0                 # Last bit for special markers
            index      = (special*1)*((chan==63)*1)                           # Find overflow locations
            special    = (special*1)*chan

        elif record_type == 'rtHydraHarpT2':

            print('TCSPC Hardware: {}'.format(record_type[2:]))

            #   +----------------------+ T3 32 bit record  +---------------------+
            #   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x| --> 32 bit record
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | | | | |x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  --> Sync
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | |x|x|x|x|x|x| | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Spectral/TCSPC input Channel
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   |x| | | | | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Special markers
            #   +-------------------------------+  +-------------------------------+
            WRAPAROUND = 33552000                                               # After this sync counter will overflow
            sync       = np.bitwise_and(t3records, 33554431)                    # Lowest 25 bits
            chan       = np.bitwise_and(np.right_shift(t3records, 25),63)       # Next 6 bits 
            tcspc      = np.bitwise_and(chan, 15)                               
            special    = np.bitwise_and(np.right_shift(t3records, 31),1)        # Last bit for special markers
            index      = (special*1) * ((chan==63)*1)                             # Find overflow locations
            special    = (special*1)*chan

        elif record_type in ['rtHydraHarp2T2', 'rtTimeHarp260NT2', 'rtTimeHarp260PT2','rtMultiHarpNT2']:

            print('TCSPC Hardware: {}'.format(record_type[2:]))

            #   +----------------------+ T3 32 bit record  +---------------------+
            #   |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x| --> 32 bit record
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | | | | | | | |x|x|x|x|x|x|x|x|x|  |x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|x|  --> Sync
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   | |x|x|x|x|x|x| | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Spectral/TCSPC input Channel
            #   +-------------------------------+  +-------------------------------+
            #   +-------------------------------+  +-------------------------------+
            #   |x| | | | | | | | | | | | | | | |  | | | | | | | | | | | | | | | | |  --> Special markers
            #   +-------------------------------+  +-------------------------------+

            WRAPAROUND = 33554432                                               # After this sync counter will overflow
            sync       = np.bitwise_and(t3records, 33554431)                    # Lowest 25 bits
            chan       = np.bitwise_and(np.right_shift(t3records, 25),63)       # Next 6 bits 
            tcspc      = np.bitwise_and(chan, 15)                               
            special    = np.bitwise_and(np.right_shift(t3records, 31),1)        # Last bit for special markers
            index      = (special*1) * ((chan==63)*1)                            # Find overflow locations
            special    = (special*1)*chan

        else:
            print('Illegal RecordType!')
            exit(0)



        # Fill in the correct sync values for overflow location    
        #sync[np.where(index == 1)] = 1 # assert values of sync = 1 just right after overflow to avoid any overflow-correction instability in next step
        if record_type in ['rtHydraHarp2T3','rtTimeHarp260PT3','rtMultiHarpNT3']:
            sync    = sync + (WRAPAROUND*np.cumsum(index*sync)) # For HydraHarp V1 and TimeHarp260 V1 overflow corrections 
        else:
            sync    = sync + (WRAPAROUND*np.cumsum(index)) # correction for overflow to sync varibale

        sync     = np.delete(sync, np.where(index == 1), axis = 0)
        tcspc    = np.delete(tcspc, np.where(index == 1), axis = 0)
        chan     = np.delete(chan, np.where(index == 1), axis = 0)
        special  = np.delete(special, np.where(index == 1), axis = 0)
             
        del index

        # Convert to appropriate data type to save memory

        self.sync    = sync.astype(np.uint64, copy=False)
        self.tcspc   = tcspc.astype(np.uint16, copy=False)
        self.channel = chan.astype(np.uint8,  copy=False)
        self.special = special.astype(np.uint8, copy=False)
        print("Raw Data has been Read!\n")

        return None
    
    def get_flim_data_stack(self): 
        
        # Check if it's FLIM image
        if self.head["Measurement_SubMode"] == 0:
            raise IOError("This is not a FLIM PTU file.!!! \n")
            sys.exit()
        elif (self.head["ImgHdr_Ident"] == 1) or (self.head["ImgHdr_Ident"] == 5):
            raise IOError("Piezo Scanner Data Reader Not Implemented Yet!!! \n")
            sys.exit()
        else:
        # Create numpy array of important variables to be passed into numba accelaratd get_flim_data_stack_static function
        # as numba doesn't recognizes python dict type files
        # Check

            header_variables  = np.array([self.head["ImgHdr_Ident"], self.head["MeasDesc_Resolution"],self.head["MeasDesc_GlobalResolution"],self.head["ImgHdr_PixX"], self.head["ImgHdr_PixY"], self.head["ImgHdr_LineStart"],self.head["ImgHdr_LineStop"], self.head["ImgHdr_Frame"]],dtype = np.uint64)
        
        sync        = self.sync 
        tcspc       = self.tcspc
        channel     = self.channel 
        special     = self.special 
        
        del self.sync, self.tcspc, self.channel , self.special
        
        flim_data_stack = get_flim_data_stack_static(sync, tcspc, channel, special, header_variables)
        
        if flim_data_stack.ndim == 4:
            
            tmp_intensity_image  = np.sum(flim_data_stack, axis = 3) # sum across tcspc bin
            intensity_image      = np.sum(tmp_intensity_image, axis  = 2)# sum across spectral channels
            
        elif flim_data_stack.ndim == 3:
            
            intensity_image  = np.sum(flim_data_stack, axis = 3) # sum across tcspc bin, only 1 detection channel
        
        return flim_data_stack, intensity_image

@njit
def get_lifetime_image(flim_data_stack,channel_number,timegating_start1,timegating_stop1,meas_resolution,estimated_irf):

    work_data  = flim_data_stack[:,:,channel_number,timegating_start1:timegating_stop1]
    bin_range = np.reshape(np.linspace(0,timegating_stop1,timegating_stop1),(1,1,timegating_stop1))

    fast_flim = (np.sum(work_data*bin_range,axis = 2)*meas_resolution)/np.sum(work_data,axis = 2)
    
    return fast_flim
