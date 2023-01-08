WITH ORDER_DATA AS (

  WITH STAGE01 AS (
  SELECT 
    TIME_BUNDLE_ID,
    C.METRO_ID,
    B.NG_ORDER_ID,
    CASE WHEN B.BUNDLE_TYPE IN ('TARP', 'TLMD') THEN B.BUNDLE_TYPE ELSE 'STANDARD' END AS DELIV_TYPE,
    --CONCAT(DELIV_TYPE, ' ', RETAILER, ' ', METRO, ' ', ADDRESS_1,' ', COALESCE(ADDRESS_2, ''), ' ', DEST_X, ' ', DEST_Y, ' ', DEST_Z) AS DELIVERY_INFO,
    LOCAL_CREATED_AT::DATE AS LOCAL_CREATED_DATE,
    LOCAL_CREATED_AT,
    CASE WHEN A.PRESCRIPTION_CERTIFICATION_REQUIRED = TRUE THEN 1 ELSE 0 END AS RX_FLG,
    CASE WHEN TRIM(ADDRESS_2) IS NOT NULL THEN 1 ELSE 0 END AS APT_FLG
  FROM DATA_SCIENCE.ORDER_STATS AS A
  INNER JOIN DATA_SCIENCE.OPSML_DELIV_ORDERS AS B
      ON A.NG_ORDER_ID = B.NG_ORDER_ID
  INNER JOIN NG_VIEWS.METROPOLIS_STORE_LOCATION AS C
     ON A.STORE_LOCATION_ID = C.STORE_LOCATION_ID  
  WHERE 1=1
      AND SHOPPER_EXPERIENCE = 'delivery'
      AND B.BUNDLE_TYPE = 'TARP'
  --GROUP BY 
    --TIME_BUNDLE_ID
  )

    SELECT 
    TIME_BUNDLE_ID,
    METRO_ID,
    --ARRAY_UNIQUE_AGG(DELIVERY_INFO) AS DELIVERY_INFO,
    ARRAY_AGG(NG_ORDER_ID) AS ORDER_IDS,
    SUM(RX_FLG) AS NBR_RX,
    SUM(APT_FLG) AS NBR_APT,
    MAX(LOCAL_CREATED_DATE) AS LOCAL_CREATED_DATE,
    max(LOCAL_CREATED_AT) AS LOCAL_CREATED_AT
    FROM STAGE01
    GROUP BY 
      TIME_BUNDLE_ID,
      METRO_ID

),

STAGE02 AS (
SELECT 
A.TIME_BUNDLE_ID,
B.LOCAL_CREATED_DATE,
B.LOCAL_CREATED_AT,
B.METRO_ID,
CASE WHEN A.BUNDLE_TYPE IN ('TARP', 'TLMD') THEN A.BUNDLE_TYPE ELSE 'STANDARD' END AS BUNDLE_TYPE,
B.ORDER_IDS,
A.NBR_ADDRESSES,
A.NBR_ORDERS,
A.DROP_OFF_TIME, 
A.EVAL_OUTLIER,
A.EVAL_FLG,
B.NBR_RX,
B.NBR_APT,
--ARRAY_TO_STRING(DELIVERY_INFO, '. ') AS DELIVERY_INFO,
DATEDIFF(WEEK, LOCAL_CREATED_DATE, CURRENT_DATE) AS DATE_DIFF
FROM DATA_SCIENCE.OPSML_BUNDLES_DROP_OFF_TIME AS A
LEFT JOIN ORDER_DATA  AS B
    ON A.TIME_BUNDLE_ID = B.TIME_BUNDLE_ID
LEFT JOIN (
          SELECT 
          TIME_BUNDLE_ID,
          CASE WHEN SUM(MOVN_2_FAST + MOVN_2_SLOW) > 0 THEN 1 ELSE 0 END AS RMV_FLG
          FROM DATA_SCIENCE.OPSML_GEO_ORDER_VALIDATIONS
          GROUP BY
             TIME_BUNDLE_ID
    ) AS C
  ON A.TIME_BUNDLE_ID = C.TIME_BUNDLE_ID
WHERE 1=1
    AND SHOPPER_EXPERIENCE = 'delivery'
    AND (EVAL_FLG = 1 OR C.RMV_FLG = 0)
GROUP BY 
    A.TIME_BUNDLE_ID,
    B.LOCAL_CREATED_DATE,
    B.LOCAL_CREATED_AT,
    B.METRO_ID,
    A.BUNDLE_TYPE,
    B.ORDER_IDS,
    A.NBR_ADDRESSES,
    A.NBR_ORDERS,
    A.DROP_OFF_TIME, 
    A.EVAL_FLG,
    A.EVAL_OUTLIER,
    NBR_RX,
    NBR_APT
    --DELIVERY_INFO
),

ORDER_IDS AS (
SELECT 
TIME_BUNDLE_ID,
CAST(NG_ORD.VALUE AS STRING) NG_ORDER_ID
FROM STAGE02,
TABLE(FLATTEN(ORDER_IDS)) NG_ORD
WHERE NBR_ORDERS =1
),


STAGE03 AS (
SELECT
TIME_BUNDLE_ID,
LOCAL_CREATED_DATE,
LOCAL_CREATED_AT,
METRO_ID,
BUNDLE_TYPE,
NBR_ADDRESSES,
NBR_ORDERS,
DROP_OFF_TIME/60 AS DROP_OFF_TIME,
EVAL_FLG,
EVAL_OUTLIER,
NBR_RX,
NBR_APT,
--DELIVERY_INFO,
DATE_DIFF,
APPROX_PERCENTILE(DROP_OFF_TIME, 0.25) OVER(PARTITION BY BUNDLE_TYPE, EVAL_FLG, NBR_ADDRESSES) PERC_25,
APPROX_PERCENTILE(DROP_OFF_TIME, 0.75) OVER(PARTITION BY BUNDLE_TYPE, EVAL_FLG, NBR_ADDRESSES) PERC_75,
ABS(PERC_75 - PERC_25) AS IQR,
CASE 
   WHEN DROP_OFF_TIME < (PERC_25 - (1.5 *IQR)) THEN 1
   WHEN DROP_OFF_TIME > (PERC_75 + (1.5 *IQR)) THEN 1
  ELSE 0 END AS TRAIN_OUTLIER,
SIN(2*PI()*(B.DAY_OF_WEEK_NUM/7)) SIN_DAY_WK,
COS(2*PI()*(B.DAY_OF_WEEK_NUM/7)) COS_DAY_WK,
SIN(2*PI()*(B.CALENDAR_DAY_OF_YEAR/365)) SIN_DAY_YR,
COS(2*PI()*(B.CALENDAR_DAY_OF_YEAR/365)) COS_DAY_YR,
SIN(2*PI()*(B.CALENDAR_MONTH/12)) SIN_MTH,
COS(2*PI()*(B.CALENDAR_MONTH/12)) COS_MTH,
SIN(2*PI()*(B.CALENDAR_WEEK_OF_YEAR/52)) SIN_WK_YR,
COS(2*PI()*(B.CALENDAR_WEEK_OF_YEAR/52)) COS_WK_YR
FROM STAGE02 AS A
INNER JOIN WAREHOUSE.DIM_DATE AS B
    ON A.LOCAL_CREATED_DATE = B.DATE_VALUE
WHERE 1=1
    --AND DELIVERY_INFO IS NOT NULL
    AND (EVAL_FLG = 0 OR (EVAL_FLG = 1 AND BUNDLE_TYPE = 'TARP'))
),

--DAILY_AVG AS (
--SELECT
--BUNDLE_TYPE,
--LOCAL_CREATED_DATE,
--METRO,
--AVG(DROP_OFF_TIME/NBR_ADDRESSES) DROP_PER_ADDRESS
--FROM STAGE03
--  GROUP BY 
--    BUNDLE_TYPE,
--    LOCAL_CREATED_DATE,
--    METRO
--),

SAMPLE_ AS (
SELECT 
*,
ROW_NUMBER() OVER(PARTITION BY BUNDLE_TYPE, DATE_DIFF ORDER BY RANDOM()) AS SEQ
FROM STAGE03
),

KEEP_FLG AS (
SELECT
BUNDLE_TYPE,
DATE_DIFF,
MAX(SEQ) AS LEN_,
CASE WHEN DATE_DIFF <= 12 THEN 1 * LEN_
     WHEN DATE_DIFF >12 AND DATE_DIFF <= 24 THEN .90 * LEN_
     WHEN DATE_DIFF >24 AND DATE_DIFF <= 52 THEN .75 * LEN_
     ELSE .50 * LEN_ END AS KEEP_NUM
FROM SAMPLE_
GROUP BY 
  BUNDLE_TYPE,
  DATE_DIFF
),

STAGE04 AS (
SELECT A.*
FROM SAMPLE_ AS A
LEFT JOIN KEEP_FLG AS B
    ON A.BUNDLE_TYPE = B.BUNDLE_TYPE
    AND A.DATE_DIFF = B.DATE_DIFF
WHERE 1=1
  --AND (A.BUNDLE_TYPE = 'STANDARD' AND SEQ <= (KEEP_NUM*.2))
  OR A.BUNDLE_TYPE = 'TARP'
  --OR A.BUNDLE_TYPE = 'TLMD'
),

final_data as (
SELECT 
A.TIME_BUNDLE_ID,
A.LOCAL_CREATED_DATE,
A.LOCAL_CREATED_AT,
A.METRO_ID,
A.BUNDLE_TYPE,
A.NBR_ADDRESSES,
A.NBR_ORDERS,
A.DROP_OFF_TIME,
A.EVAL_FLG,
A.EVAL_OUTLIER,
A.NBR_RX,
A.NBR_APT,
--A.DELIVERY_INFO,
A.DATE_DIFF,
A.TRAIN_OUTLIER,
A.SIN_DAY_WK,
A.COS_DAY_WK,
A.SIN_DAY_YR,
A.COS_DAY_YR,
A.SIN_MTH,
A.COS_MTH,
A.SIN_WK_YR,
A.COS_WK_YR
--AVG(CASE WHEN B.LOCAL_CREATED_DATE BETWEEN DATEADD('WEEK', -2, A.LOCAL_CREATED_DATE) AND A.LOCAL_CREATED_DATE THEN DROP_PER_ADDRESS ELSE NULL END) AS R2WK_DROP_PER_ADD,
--AVG(CASE WHEN B.LOCAL_CREATED_DATE BETWEEN DATEADD('WEEK', -4, A.LOCAL_CREATED_DATE) AND DATEADD('WEEK', -2, A.LOCAL_CREATED_DATE) THEN DROP_PER_ADDRESS ELSE NULL END) AS R4WK_DROP_PER_ADD,
--(R2WK_DROP_PER_ADD - R4WK_DROP_PER_ADD)/R4WK_DROP_PER_ADD AS RPERC_DROP
FROM STAGE04 AS A
--LEFT JOIN DAILY_AVG AS B
  --ON A.BUNDLE_TYPE = B.BUNDLE_TYPE
  --AND A.METRO = B.METRO
  --AND B.LOCAL_CREATED_DATE BETWEEN DATEADD('WEEK', -8, A.LOCAL_CREATED_DATE) AND A.LOCAL_CREATED_DATE
GROUP BY 
    A.TIME_BUNDLE_ID,
    A.LOCAL_CREATED_DATE,
    A.LOCAL_CREATED_AT,
    A.METRO_ID,
    A.BUNDLE_TYPE,
    A.NBR_ADDRESSES,
    A.NBR_ORDERS,
    A.DROP_OFF_TIME,
    A.EVAL_FLG,
    A.EVAL_OUTLIER,
    A.NBR_RX,
    A.NBR_APT,
    --A.DELIVERY_INFO,
    A.DATE_DIFF,
    A.TRAIN_OUTLIER,
    A.SIN_DAY_WK,
    A.COS_DAY_WK,
    A.SIN_DAY_YR,
    A.COS_DAY_YR,
    A.SIN_MTH,
    A.COS_MTH,
    A.SIN_WK_YR,
    A.COS_WK_YR
),

METRO_LAT_LON AS (
  SELECT 
  METRO_ID, 
  AVG(ADDRESS_LATITUDE) AS METRO_LAT, 
  AVG(ADDRESS_LONGITUDE) AS METRO_LON
  FROM (
  SELECT *
  from NG_VIEWS.METROPOLIS_STORE_LOCATION
  WHERE 1=1
      AND ACTIVE = TRUE
  QUALIFY ROW_NUMBER() OVER(PARTITION BY  ZONE_ID, METRO_ID, STORE_LOCATION_ID ORDER BY LAUNCH_DATE DESC) = 1
  )
  GROUP BY METRO_ID
  )


select A.*,
B.NG_ORDER_ID,
6371 * COS(RADIANS(METRO_LAT)) * COS(RADIANS(METRO_LON)) METRO_X,
6371 * COS(RADIANS(METRO_LAT)) * SIN(RADIANS(METRO_LON)) METRO_Y,
6371 * SIN(RADIANS(METRO_LAT)) METRO_Z,
CASE WHEN NBR_APT > 0 THEN 1 ELSE 0 END AS APT_FLG
FROM FINAL_DATA AS A
LEFT JOIN ORDER_IDS AS B
  ON A.TIME_BUNDLE_ID = B.TIME_BUNDLE_ID
LEFT JOIN METRO_LAT_LON AS C
  ON A.METRO_ID = C.METRO_ID
limit 20000
  