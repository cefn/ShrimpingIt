#include <Tone.h>

/** 
This is a clone of the logic of MB Games' Simon memory game

It is intended to drive an example circuit developed for the @ShrimpingIt
project, which documents how to make extremely low cost and simple
Arduino-compatible circuits. 

The Simon circuit can be constructed for a total cost of less than £3 including 
batteries. It relies on a neat trick which means LEDs can be used directly as 
illuminated buttons, massively reducing the cost of fabrication.

Things to do: add melodies for transitions between game modes.
Introduce RTTTL reading logic so people can easily change the melodies.
Flip common led and button ground rail for a single rail running the length of the board below the chip.
Align spot cuts for series and symmetry 
Remove delay() clause in setMode()

*/

//the pins used to provide the 
//backlit pads for the Simon Game
#define NUMPADS 4
int buttons[] = {3,7,10,A1};
int lights[] = {2,5,12,A2};

//the storage used for the pad 
//sequence you have to follow 
#define MAXSEQUENCE 256
int sequence[MAXSEQUENCE];
int sequencePos = 0;
int sequenceLength = 1;

//These should in the end use RTTTL to define any tune
int successTune[] = {NOTE_C3, NOTE_E3, NOTE_A3, NOTE_G2};
int failureTune[] = {NOTE_G2,NOTE_A3,NOTE_E3,NOTE_C3};

#define SHOW 1
#define HEAR 2
int gameMode = SHOW;

int speakerPin =11;
Tone speaker;
int tones[] = {NOTE_C3, NOTE_E3, NOTE_A3, NOTE_G2};
int toneFailure = NOTE_C3;

unsigned long lastTriggered = 0;
int lastPadPressed = -1;

long toneLength = 400;
long restLength = 100;
//long failLength = 2000;

unsigned long noteStarted = -1;
int noteDuration = -1;

void setup(){
  Serial.begin(9600);
	speaker.begin(speakerPin);
	randomSeed(analogRead(5));
	randomiseSequence();
	for(int padIdx = 0; padIdx < NUMPADS; padIdx++){
		pinMode(buttons[padIdx], INPUT);
		pinMode(lights[padIdx],OUTPUT);
	}
}

void loop(){
  
	//decide if anything needs doing, based on current mode
	if(gameMode == SHOW){
		//simon is playing a sequence to memorise
		showSequence();
	}
	else if(gameMode==HEAR){
		//not teaching but waiting for presses
		hearSequence();
	}
}

void randomiseSequence(){
	for(int sequenceIdx = 0; sequenceIdx < MAXSEQUENCE; sequenceIdx++){
		sequence[sequenceIdx] = random(NUMPADS);
	}
}

void lightPad(int padIdx){
	digitalWrite(lights[padIdx], HIGH);
}

void darkenPads(){
	for(int padIdx = 0; padIdx < NUMPADS; padIdx++){
		digitalWrite(lights[padIdx], LOW);
	}	
}

int getPadPressed(){
	for(int padIdx = 0; padIdx < NUMPADS; padIdx++){
		if(digitalRead(buttons[padIdx]) == LOW){
			return padIdx;
		}
	}
	return -1;
}

void setMode(int mode){
  if(mode == SHOW){
    delay(toneLength);    
  }
  stopNotes();
  darkenPads();
  gameMode = mode;
  sequencePos = 0;
}

void resetGame(){
        sequenceLength = 1;
	randomiseSequence();
        setMode(SHOW);
}

void showSequence(){
	//get a timestamp for this iteration
	long now = millis();

	//consider progressing the tune and lights
	if(!isNotePlaying()){
                Serial.println("Speaker not playing");
		//no sound playing, test if one should begin
		if(now - lastTriggered > (toneLength + restLength) || lastTriggered == 0){
                        Serial.println("Last note finished");
			//progress sequence, play note and illuminate light
			if(sequencePos < sequenceLength){
                              Serial.print("Playing new note: ");
                              Serial.println(sequence[sequencePos]);
				//still more of target melody to play
				playNote(tones[sequence[sequencePos]], toneLength);
				digitalWrite(lights[sequence[sequencePos]], HIGH);
				lastTriggered = now;
				sequencePos += 1;
			}
			else{
                              Serial.println("Played all the notes in this round");
				//target melody is complete
				//now check the player can copy it
                                setMode(HEAR);
			}				
		}
	}
	else{
          Serial.println("Speaker playing");

		//sound is playing, check if it should stop
		if(now - lastTriggered > toneLength){
                        Serial.println("Stopping note");
			//stop sound and extinguish lights
                        stopNotes();
			darkenPads();
		}
	}
}

void hearSequence(){

	int padPressed = getPadPressed(); 
        Serial.print("Pad pressed");
        Serial.println(padPressed);
	
	if(padPressed != lastPadPressed){
		//pad state has changed
		if(lastPadPressed == -1){
			//a pad was pressed, so light that pad
			lightPad(padPressed);
			if(padPressed == sequence[sequencePos]){
                                Serial.println("Note is correct, incrementing sequence");
				//if correct target play successful tone
				playNote(tones[padPressed], toneLength);
				//extend the melody and teach again
				sequencePos += 1;
                                if(sequencePos == sequenceLength){
                                  //completed this round
                                  sequenceLength += 1;
  				  if(sequenceLength != MAXSEQUENCE){
                                    //not completed game, so re-run
                                    Serial.println("Demonstrating longer sequence");
                                    setMode(SHOW);
  				  }
                                  else{
                                    Serial.println("Game is complete");
                                    //completed game!
                                    //TODO some kind of fanfare
                                    resetGame();
                                  }
                                }
			}
			else{
                                Serial.println("Note is wrong, resetting game");
  				//play failure tone
				playNote(toneFailure, toneLength);
				//start teaching a new random sequence
				resetGame();
			}
			lastTriggered = millis();
		}
		else{
			//a pad was released
			//turn off lights and silence
			stopNotes;
			darkenPads();
		}
		lastPadPressed = padPressed;
	}
}

/*
void testPattern(){
  int padPressed = getPadPressed();
  Serial.print("Pad pressed:");
  Serial.println(padPressed);
  digitalWrite(lights[tmpLight], LOW);
  tmpLight = (tmpLight + 1) % NUMPADS;
  digitalWrite(lights[tmpLight], HIGH);
  playNote(tones[tmpLight]);
  delay(200);
}
*/

void playNote(int pitch){
  noteStarted = millis();
  noteDuration = -1;
  speaker.play(pitch);
}

void playNote(int pitch, int duration){
  noteStarted = millis();
  noteDuration = duration;
  speaker.play(pitch, duration);  
}

void stopNotes(){
  noteStarted = -1;
  noteDuration = -1;
  speaker.stop();
}

boolean isNotePlaying(){
  return noteStarted != -1 &&
  (millis() - noteStarted) < noteDuration;
}
