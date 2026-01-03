import json

#This class is effectively a container for all the parameters being used, unique to each user, for the calculation of the journeys
class Parameters():
    def __init__(
            self,
            CHANGING_TIME, #This is the additional take added to each journey
            MAX_TIME_WINDOW, #This is the maximum time from the peak that if an event falls within it, will be considered in the calculations for crowding
            rawArrivalPeakOffset, #This is the raw number in minutes of the peak of crowding from the start of a game
            rawDeparturePeakOffset, #This is the raw number in minutes of the peak of crowding from the end of a game
            ATTENDANCE, #This is the proportion of the capacity of the stadium that will attend the event (0-1)
            TRAIN_PROPORTION, #This is the proportion of people that attend the game that will use TfL rain services (0-1)
            SIGMA_FACTOR,
            MINIMUM_PEOPLE,
            PERSON_DELAY,
            PROPAGATION_FACTOR,
            WALKING_TIME,
            WALKING_SPEED,
            NORMAL,
            SLIGHTLY,
            BUSY
    ):
        self.CHANGING_TIME = CHANGING_TIME
        self.MAX_TIME_WINDOW = MAX_TIME_WINDOW
        self.rawArrivalPeakOffset = rawArrivalPeakOffset
        self.rawDeparturePeakOffset = rawDeparturePeakOffset
        self.ATTENDANCE = ATTENDANCE
        self.TRAIN_PROPORTION = TRAIN_PROPORTION
        self.SIGMA_FACTOR = SIGMA_FACTOR
        self.MINIMUM_PEOPLE = MINIMUM_PEOPLE
        self.PERSON_DELAY = PERSON_DELAY
        self.PROPAGATION_FACTOR = PROPAGATION_FACTOR
        self.WALKING_TIME = WALKING_TIME
        self.WALKING_SPEED = WALKING_SPEED
        self.NORMAL = NORMAL
        self.SLIGHTLY = SLIGHTLY
        self.BUSY = BUSY

        self.arrivalWindowMinutes = None
        self.departureWindowMinutes = None
        self.arrivalPeakOffset = None
        self.departurePeakOffset = None
        self.arrivalMinutesOffset = None
        self.departureMinutesOffset = None

    # When I was initially writing the program, window minutes for both arrival and departure were entered differently, so the program is written with the assumpton that they can be different, when in reality they are the same, so here both the arrival and departure window minutes are set to the same max time window that is passed in
    def calculateWindow(self):
        self.arrivalWindowMinutes = self.MAX_TIME_WINDOW
        self.departureWindowMinutes = self.MAX_TIME_WINDOW

    #Sets the
    def calculatePeakOffset(self):
        import datetime
        self.arrivalPeakOffset = datetime.timedelta(self.rawArrivalPeakOffset)
        self.departurePeakOffset = datetime.timedelta(self.rawDeparturePeakOffset)

    def calculateMinutesOffset(self):
        self.arrivalMinutesOffset = self.arrivalPeakOffset.total_seconds() / 60
        self.departureMinutesOffset = self.departurePeakOffset.total_seconds() / 60


class AccountCreationParameters(Parameters):
    def __init__(self, defaultParameters):
        super().__init__(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        with open(defaultParameters, 'r') as file:
            rawData = json.load(file)

        for key, value in rawData.items():
            setattr(self, key, value)