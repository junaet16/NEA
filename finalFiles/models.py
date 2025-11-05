from sqlalchemy import Column, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class StationModel(Base):
    __tablename__ = "Stations"

    NaPTAN = Column(Text, primary_key=True)
    StationName = Column(Text)
    Latitude = Column(Float)
    Longitude = Column(Float)

    # Relationships
    lines = relationship("StationLineRelationshipModel", back_populates="station")
    connections_from = relationship(
        "ConnectionModel", foreign_keys="ConnectionModel.StationA", back_populates="station_a"
    )
    connections_to = relationship(
        "ConnectionModel", foreign_keys="ConnectionModel.StationB", back_populates="station_b"
    )
    venue_relationships = relationship("VenueStationRelationshipModel", back_populates="station")


class LineModel(Base):
    __tablename__ = "Lines"

    LineID = Column(Text, primary_key=True)
    LineName = Column(Text)
    AverageSpeed = Column(Text)

    stations = relationship("StationLineRelationshipModel", back_populates="line")
    connections = relationship("ConnectionModel", back_populates="line")


class StationLineRelationshipModel(Base):
    __tablename__ = "StationLineRelationships"

    NaPTAN = Column(Text, ForeignKey("Stations.NaPTAN"), primary_key=True)
    LineID = Column(Text, ForeignKey("Lines.LineID"), primary_key=True)

    station = relationship("StationModel", back_populates="lines")
    line = relationship("LineModel", back_populates="stations")


class ConnectionModel(Base):
    __tablename__ = "Connections"

    StationA = Column(Text, ForeignKey("Stations.NaPTAN"), primary_key=True)
    StationB = Column(Text, ForeignKey("Stations.NaPTAN"), primary_key=True)
    LineID = Column(Text, ForeignKey("Lines.LineID"), primary_key=True)
    BaseTravelTime = Column(Float)

    station_a = relationship("StationModel", foreign_keys=[StationA], back_populates="connections_from")
    station_b = relationship("StationModel", foreign_keys=[StationB], back_populates="connections_to")
    line = relationship("LineModel", back_populates="connections")


class VenueModel(Base):
    __tablename__ = "Venues"

    VenueName = Column(Text, primary_key=True)
    Capacity = Column(Integer)
    Latitude = Column(Float)
    Longitude = Column(Float)

    station_relationships = relationship("VenueStationRelationshipModel", back_populates="venue")
    events = relationship("EventModel", back_populates="venue")
    teams = relationship("TeamModel", back_populates="venue")  # optional, inferred


class VenueStationRelationshipModel(Base):
    __tablename__ = "VenueStationRelationships"

    VenueName = Column(Text, ForeignKey("Venues.VenueName"), primary_key=True)
    NaPTAN = Column(Text, ForeignKey("Stations.NaPTAN"), primary_key=True)

    venue = relationship("VenueModel", back_populates="station_relationships")
    station = relationship("StationModel", back_populates="venue_relationships")


class EventModel(Base):
    __tablename__ = "Events"

    VenueName = Column(Text, ForeignKey("Venues.VenueName"), primary_key=True)
    Date = Column(Text, primary_key=True)
    Time = Column(Text)
    HomeTeam = Column(Text)
    AwayTeam = Column(Text)
    EventName = Column(Text)
    Duration = Column(Integer)

    venue = relationship("VenueModel", back_populates="events")


class UserModel(Base):
    __tablename__ = "Users"

    UserID = Colum