#g++ actual.cpp -o actual_video_central `pkg-config --cflags --libs opencv4` -lwiringPi
#g++ actual.cpp -o actual `pkg-config --cflags --libs opencv4` -lwiringPi
g++ actual.cpp -o actual `pkg-config --cflags --libs opencv4` -lwiringPi

