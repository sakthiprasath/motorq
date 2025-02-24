CREATE TABLE conferences (
    conference_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE conference_slots (
    slot_id SERIAL PRIMARY KEY,
    conference_id INT NOT NULL,
    slot_time TIMESTAMP NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    available_slots INT NOT NULL CHECK (available_slots >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conference_id) REFERENCES conferences(conference_id) ON DELETE CASCADE
);

CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    slot_id INT NOT NULL,
    user_id INT NOT NULL,
    booking_status VARCHAR(20) NOT NULL CHECK (booking_status IN ('booked', 'canceled')),
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    canceled_time TIMESTAMP,
    conference_id INT,
    FOREIGN KEY (slot_id) REFERENCES conference_slots(slot_id) ON DELETE CASCADE,
    FOREIGN KEY (conference_id) REFERENCES conferences(conference_id)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE OR REPLACE FUNCTION decrease_available_slots()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conference_slots
    SET available_slots = available_slots - 1
    WHERE slot_id = NEW.slot_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER booking_inserted
AFTER INSERT ON bookings
FOR EACH ROW
WHEN (NEW.booking_status = 'booked')
EXECUTE FUNCTION decrease_available_slots();


CREATE OR REPLACE FUNCTION increase_available_slots()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conference_slots
    SET available_slots = available_slots + 1
    WHERE slot_id = OLD.slot_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER booking_canceled
AFTER UPDATE ON bookings
FOR EACH ROW
WHEN (OLD.booking_status = 'booked' AND NEW.booking_status = 'canceled')
EXECUTE FUNCTION increase_available_slots();

