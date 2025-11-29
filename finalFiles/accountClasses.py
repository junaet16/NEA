import json


class Parameters():
    def __init__(
            self,
            CHANGING_TIME,
            MAX_TIME_WINDOW,
            rawArrivalPeakOffset,
            rawDeparturePeakOffset,
            ATTENDANCE,
            TRAIN_PROPORTION,
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

    def calculateWindow(self):
        self.arrivalWindowMinutes = self.MAX_TIME_WINDOW
        self.departureWindowMinutes = self.MAX_TIME_WINDOW

    def calculatePeakOffset(self):
        import datetime
        self.arrivalPeakOffset = datetime.timedelta(minutes=15)
        self.departurePeakOffset = datetime.timedelta(minutes=15)

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