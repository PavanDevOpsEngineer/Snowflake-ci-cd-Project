-- ============================================
-- Git Integration Setup for Public Repository
-- Connect Snowsight Workspace to GitHub (no auth required)
-- Run as ACCOUNTADMIN
-- ============================================

-- Step 1: Create API Integration (no authentication needed for public repos)
CREATE OR REPLACE API INTEGRATION GITHUB_CICD_INTEGRATION
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/PavanDevOpsEngineer')
  ENABLED = TRUE;

-- Step 2: Create Git Repository object in Snowflake
CREATE OR REPLACE GIT REPOSITORY DEV_DB.PUBLIC.SNOWFLAKE_CICD_REPO
  API_INTEGRATION = GITHUB_CICD_INTEGRATION
  ORIGIN = 'https://github.com/PavanDevOpsEngineer/Snowflake-ci-cd-Project.git';

-- Step 3: Fetch latest from remote
ALTER GIT REPOSITORY DEV_DB.PUBLIC.SNOWFLAKE_CICD_REPO FETCH;

-- Step 4: Verify - List branches
SHOW GIT BRANCHES IN DEV_DB.PUBLIC.SNOWFLAKE_CICD_REPO;

-- Step 5: Verify - List files in main branch
LIST @DEV_DB.PUBLIC.SNOWFLAKE_CICD_REPO/branches/develop/;
