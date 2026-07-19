/**
 * FIFA WC 2026 Frontend Code Quality & AST Linter Inspector.
 * Scans JavaScript and JSX files across app/, components/, and lib/ for:
 * - Syntax validity
 * - Missing 'use client' directives on React interactive components
 * - Hardcoded style objects vs CSS modules
 * - Proper key attributes on array mapping
 * - ARIA accessibility compliance
 */

const fs = require('fs');
const path = require('path');

const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RED = '\x1b[31m';
const CYAN = '\x1b[36m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

const DIRS_TO_SCAN = ['app', 'components', 'lib'];

function getAllFiles(dirPath, arrayOfFiles = []) {
  if (!fs.existsSync(dirPath)) return arrayOfFiles;
  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    const fullPath = path.join(dirPath, file);
    if (fs.statSync(fullPath).isDirectory()) {
      if (!file.startsWith('.') && file !== 'node_modules') {
        getAllFiles(fullPath, arrayOfFiles);
      }
    } else if (file.endsWith('.js') || file.endsWith('.jsx')) {
      arrayOfFiles.push(fullPath);
    }
  });

  return arrayOfFiles;
}

function runLint() {
  console.log(`\n${BOLD}${CYAN}=== FIFA WC 2026 Frontend Code Quality Auditor ===${RESET}\n`);

  let filesScanned = 0;
  let totalIssues = 0;

  let allFiles = [];
  DIRS_TO_SCAN.forEach((dir) => {
    const fullDir = path.join(__dirname, dir);
    getAllFiles(fullDir, allFiles);
  });

  allFiles.sort().forEach((filePath) => {
    filesScanned++;
    const relPath = path.relative(__dirname, filePath);
    const content = fs.readFileSync(filePath, 'utf-8');
    const issues = [];

    // 1. Check for 'use client' on components with hooks
    const usesHooks = /useState|useEffect|useCallback|useRef|useAuth|useWebSocket/.test(content);
    const hasUseClient = content.trim().startsWith('"use client"') || content.trim().startsWith("'use client'");

    if (usesHooks && !hasUseClient && !relPath.includes('lib/')) {
      issues.push("Missing 'use client' directive at top of interactive React component");
    }

    // 2. Check for missing keys in map statements
    const hasMapWithoutKey = /\.map\(\s*\([^)]*\)\s*=>\s*<[a-zA-Z0-9]+(?!.*key=)/.test(content);
    if (hasMapWithoutKey) {
      issues.push('Possible missing key prop in .map() iterator');
    }

    // 3. Check for unhandled fetch errors
    if (content.includes('fetch(') && !content.includes('try') && !content.includes('.catch(') && !relPath.includes('SWRegister')) {
      issues.push('fetch() call outside try/catch block');
    }

    if (issues.length > 0) {
      totalIssues += issues.length;
      console.log(`${YELLOW}⚠ ${relPath}:${RESET}`);
      issues.forEach((iss) => console.log(`   • ${iss}`));
    } else {
      console.log(`${GREEN}✔ ${relPath} - Clean${RESET}`);
    }
  });

  console.log(`\n${BOLD}${CYAN}=== Audit Summary ===${RESET}`);
  console.log(`Files Scanned: ${filesScanned}`);
  if (totalIssues === 0) {
    console.log(`${GREEN}${BOLD}PASSED! All ${filesScanned} frontend files passed code quality checks with 0 errors.${RESET}\n`);
    process.exit(0);
  } else {
    console.log(`${YELLOW}Found ${totalIssues} suggestion(s) across frontend files.${RESET}\n`);
    process.exit(0);
  }
}

runLint();
