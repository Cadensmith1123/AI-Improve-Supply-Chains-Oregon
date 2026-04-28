DELIMITER $$

DROP PROCEDURE IF EXISTS clean_anon_users $$
CREATE PROCEDURE clean_anon_users(IN p_max_age_seconds INT)
BEGIN
    DROP TEMPORARY TABLE IF EXISTS _deleted_tenants;
    CREATE TEMPORARY TABLE _deleted_tenants (tenant_id BIGINT);

    INSERT INTO _deleted_tenants (tenant_id)
    SELECT tenant_id FROM users
    WHERE role = 'Anonymous'
    AND last_active < NOW() - INTERVAL p_max_age_seconds SECOND;

    DELETE FROM tenants
    WHERE tenant_id IN (SELECT tenant_id FROM _deleted_tenants);

    SELECT tenant_id FROM _deleted_tenants;
END $$

DROP PROCEDURE IF EXISTS update_user_activity $$
CREATE PROCEDURE update_user_activity(IN p_user_id BIGINT)
BEGIN
    UPDATE users SET last_active = NOW() WHERE user_id = p_user_id;
    END $$

DROP PROCEDURE IF EXISTS upgrade_anonymous_user $$
CREATE PROCEDURE upgrade_anonymous_user(
    IN p_user_id BIGINT,
    IN p_username VARCHAR(50),
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255)
)
BEGIN
    DECLARE v_tenant_id BIGINT;
    SELECT tenant_id INTO v_tenant_id FROM users WHERE user_id = p_user_id;

    UPDATE users
    SET username = p_username,
        email = p_email,
        password_hash = p_password_hash,
        role = 'User'
    WHERE user_id = p_user_id;

    UPDATE tenants
    SET name = p_username
    WHERE tenant_id = v_tenant_id;
END $$

DELIMITER ;