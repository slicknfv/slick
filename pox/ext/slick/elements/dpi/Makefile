INC=-I nDPI/src/include/
LIB=nDPI/src/lib/.libs/libndpi.a -lpcap
FLAGS=-g
pcapReader: pcapReader.c Makefile nDPI/src/lib/.libs/libndpi.a
	gcc $(FLAGS) $(INC) pcapReader.c -o pcapReader $(LIB) -lpthread

clean:
	\/bin/rm -f pcapReader
