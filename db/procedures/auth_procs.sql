DELIMITER $$

DROP PROCEDURE IF EXISTS add_user $$

CREATE PROCEDURE add_user(
    IN p_tenant_id BIGINT,
    IN p_username VARCHAR(50),
    IN p_password_hash VARCHAR(255),
    IN p_email VARCHAR(100),
    IN p_role VARCHAR(20)
)
BEGIN
    DECLARE v_new_tenant_id BIGINT;

    -- Create a tenant for this user (User IS Tenant model)
    INSERT INTO tenants (name) VALUES (p_username);
    SET v_new_tenant_id = LAST_INSERT_ID();

    INSERT INTO users (tenant_id, username, password_hash, email, role, is_active)
    VALUES (v_new_tenant_id, p_username, p_password_hash, p_email, p_role, TRUE);
    
    SELECT LAST_INSERT_ID();
END $$

DROP PROCEDURE IF EXISTS delete_user $$

CREATE PROCEDURE delete_user(
    IN p_tenant_id BIGINT,
    IN p_user_id BIGINT
)
BEGIN
    DELETE FROM users WHERE user_id = p_user_id AND tenant_id = p_tenant_id;
END $$

DROP PROCEDURE IF EXISTS get_user_by_username $$

CREATE PROCEDURE get_user_by_username(
    IN p_username VARCHAR(50)
)
BEGIN
    SELECT user_id, tenant_id, password_hash, role
    FROM users
    WHERE username = p_username;
END $$

DELIMITER ;