DELIMITER $$

DROP PROCEDURE IF EXISTS set_totp_secret $$

CREATE PROCEDURE set_totp_secret(
    IN p_user_id BIGINT,
    IN p_secret VARCHAR(32)
)
BEGIN
    UPDATE users SET totp_secret = p_secret WHERE user_id = p_user_id;
END $$

DROP PROCEDURE IF EXISTS set_totp_confirmed $$

CREATE PROCEDURE set_totp_confirmed(
    IN p_user_id BIGINT,
    IN p_confirmed BOOLEAN
)
BEGIN
    UPDATE users SET totp_confirmed = p_confirmed WHERE user_id = p_user_id;
END $$

DROP PROCEDURE IF EXISTS get_user_totp $$

CREATE PROCEDURE get_user_totp(
    IN p_user_id BIGINT
)
BEGIN
    SELECT totp_secret, totp_confirmed
    FROM users
    WHERE user_id = p_user_id;
END $$

DROP PROCEDURE IF EXISTS get_user_for_reset $$

CREATE PROCEDURE get_user_for_reset(
    IN p_username VARCHAR(50)
)
BEGIN
    SELECT user_id, totp_secret, totp_confirmed
    FROM users
    WHERE username = p_username;
END $$

DROP PROCEDURE IF EXISTS update_user_password $$

CREATE PROCEDURE update_user_password(
    IN p_user_id BIGINT,
    IN p_password_hash VARCHAR(255)
)
BEGIN
    UPDATE users SET password_hash = p_password_hash WHERE user_id = p_user_id;
END $$

DELIMITER ;
