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
    FOREIGN KEY (slot_id) REFERENCES conference_slots(slot_id) ON DELETE CASCADE
);

ALTER TABLE bookings
ADD COLUMN conference_id INT REFERENCES conferences(conference_id);

