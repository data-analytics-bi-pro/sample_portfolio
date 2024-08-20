/* Sample MS SQL Code */

-- Request: Pull the top three unique employee salaries for each department

-- Sample data from Leetcode
Employee =
| id | name  | salary | departmentId |
| -- | ----- | ------ | ------------ |
| 1  | Joe   | 85000  | 1            |
| 2  | Henry | 80000  | 2            |
| 3  | Sam   | 60000  | 2            |
| 4  | Max   | 90000  | 1            |
| 5  | Janet | 69000  | 1            |
| 6  | Randy | 85000  | 1            |
| 7  | Will  | 70000  | 1            |

Department =
| id | name  |
| -- | ----- |
| 1  | IT    |
| 2  | Sales |
1

-- My MS SQL solution code
SELECT * FROM
(
    SELECT 
        ISNULL(d.name, 'Missing Department') AS Department,
        e.name AS Employee,
        DENSE_RANK() OVER (PARTITION BY d.name ORDER BY e.salary DESC) AS "Rank",
        e.salary AS Salary
    FROM DEPARTMENT d
    FULL OUTER JOIN EMPLOYEE e
        ON e.departmentID = d.id
)
WHERE Rank <= 3;


-- Request: Find the daily cancellation rate for unbanned users between 2013-10-01 and 2013-10-03

-- Sample data from Leetcode
Trips =
| id | client_id | driver_id | city_id | status              | request_at |
| -- | --------- | --------- | ------- | ------------------- | ---------- |
| 1  | 1         | 10        | 1       | completed           | 2013-10-01 |
| 2  | 2         | 11        | 1       | cancelled_by_driver | 2013-10-01 |
| 3  | 3         | 12        | 6       | completed           | 2013-10-01 |
| 4  | 4         | 13        | 6       | cancelled_by_client | 2013-10-01 |
| 5  | 1         | 10        | 1       | completed           | 2013-10-02 |
| 6  | 2         | 11        | 6       | completed           | 2013-10-02 |
| 7  | 3         | 12        | 6       | completed           | 2013-10-02 |
| 8  | 2         | 12        | 12      | completed           | 2013-10-03 |
| 9  | 3         | 10        | 12      | completed           | 2013-10-03 |
| 10 | 4         | 13        | 12      | cancelled_by_driver | 2013-10-03 |

Users =
| users_id | banned | role   |
| -------- | ------ | ------ |
| 1        | No     | client |
| 2        | Yes    | client |
| 3        | No     | client |
| 4        | No     | client |
| 10       | No     | driver |
| 11       | No     | driver |
| 12       | No     | driver |
| 13       | No     | driver |

-- My MS SQL solution code
SELECT 
    t.request_at AS 'Day',
    ROUND(SUM(CASE WHEN t.status like '%cancelled%' THEN 1.00 ELSE 0.00 END) 
    / CAST(COUNT(t.status) AS FLOAT), 2) AS 'Cancellation Rate'
FROM Trips t
LEFT JOIN (SELECT * FROM Users WHERE role = 'client') uc
    ON uc.users_id = t.client_id
LEFT JOIN (SELECT * FROM Users WHERE role = 'driver') ud
    ON ud.users_id = t.driver_id
WHERE 
    uc.banned = 'No' AND ud.banned = 'No'
GROUP BY t.request_at;
