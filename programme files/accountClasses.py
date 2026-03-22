import json

#This class is effectively a container for all the parameters being used, unique to each user, for the calculation of the journeys
class Parameters():
    def __init__(
            self,
            CHANGING_TIME, # Extra time added to each journey (minutes)
            MAX_TIME_WINDOW, # Maximum time from the event peak to consider crowding (minutes)
            rawArrivalPeakOffset, # Minutes from event start when crowding peaks on arrival
            rawDeparturePeakOffset,  # Minutes from event end when crowding peaks on departure
            ATTENDANCE, # Proportion of stadium capacity attending (0-1)
            TRAIN_PROPORTION, # Proportion using TfL rail services (0-1)
            SIGMA_FACTOR, # Controls how tightly people cluster around the peak time — it converts a time window into a Gaussian spread
            MINIMUM_PEOPLE, # Minimum people threshold for affecting stations
            PERSON_DELAY, # Additional delay per person on journey
            PROPAGATION_FACTOR, # Factor for spreading delay across network
            WALKING_TIME, # Default walking time between station and venue (minutes)
            WALKING_SPEED, # Default walking speed (m/s)
            NORMAL, # Crowding thresholds for classification: normal (below this is normal)
            SLIGHTLY, # Crowding thresholds for classification: slightly busy (below this is slightly busy)
            BUSY # Crowding thresholds for classification: busy (below this is busy and above is severely busy)
    ):

        # Store all parameters in the object
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

        # Internal attributes for arrival/departure calculations
        self.arrivalWindowMinutes = None
        self.departureWindowMinutes = None
        self.arrivalPeakOffset = None
        self.departurePeakOffset = None
        self.arrivalMinutesOffset = None
        self.departureMinutesOffset = None


    # Sets the arrival and departure window minutes to MAX_TIME_WINDOW
    # Both windows use the same value - the programme is written to allow them to differ in future if needed
    def calculateWindow(self):
        self.arrivalWindowMinutes = self.MAX_TIME_WINDOW
        self.departureWindowMinutes = self.MAX_TIME_WINDOW


    #Converts raw peak offsets stored in minutes to timedelta objects for use in datetime arithmetic
    def calculatePeakOffset(self):
        import datetime
        self.arrivalPeakOffset = datetime.timedelta(minutes=self.rawArrivalPeakOffset)
        self.departurePeakOffset = datetime.timedelta(minutes=self.rawDeparturePeakOffset)


    # Converts the peak offsets to numeric minutes for simpler calculations
    def calculateMinutesOffset(self):
        self.arrivalMinutesOffset = self.arrivalPeakOffset.total_seconds() / 60
        self.departureMinutesOffset = self.departurePeakOffset.total_seconds() / 60



# This subclass is used when creating a new account
# It loads default parameters from a JSON file so each user starts with reasonable defaults
class AccountCreationParameters(Parameters):
    def __init__(self, defaultParameters):
        # Initialise with placeholder zeros; these will be overwritten by JSON
        super().__init__(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # Load default parameters from JSON configuration file
        with open(defaultParameters, 'r') as file:
            rawData = json.load(file)

        # Dynamically assign attributes from JSON keys
        for key, value in rawData.items():
            setattr(self, key, value)