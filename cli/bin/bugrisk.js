#!/usr/bin/env node

const { Command } = require('commander');
const axios = require('axios');
const chalk = require('chalk');
const ora = require('ora');
require('dotenv').config();

const program = new Command();

program
  .name('bugrisk')
  .description('Bug Risk NLP CLI - Code Quality Analysis')
  .version('1.0.0');

program
  .command('scan')
  .description('Scan project for code quality issues')
  .option('-p, --project <id>', 'Project ID')
  .option('-k, --api-key <key>', 'API Key')
  .option('-u, --url <url>', 'API URL', process.env.BUGRISK_API_URL || 'https://api.bugrisk.app')
  .action(async (options) => {
    const spinner = ora('Scanning project...').start();
    
    try {
      const response = await axios.post(
        `${options.url}/scan/${options.project}`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${options.apiKey || process.env.BUGRISK_API_KEY}`
          }
        }
      );
      
      spinner.succeed('Scan completed!');
      console.log(chalk.green('\n✓ Scan Results:'));
      console.log(`  Quality Score: ${chalk.bold(response.data.quality_score)}/100`);
      console.log(`  Files Analyzed: ${chalk.bold(response.data.total_files)}`);
      console.log(`  Critical Issues: ${chalk.red.bold(response.data.critical_issues)}`);
      
    } catch (error) {
      spinner.fail('Scan failed');
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

program
  .command('get-score')
  .description('Get project quality score')
  .option('-p, --project <id>', 'Project ID')
  .option('-k, --api-key <key>', 'API Key')
  .option('-u, --url <url>', 'API URL', process.env.BUGRISK_API_URL || 'https://api.bugrisk.app')
  .action(async (options) => {
    try {
      const response = await axios.get(
        `${options.url}/metrics/${options.project}`,
        {
          headers: {
            'Authorization': `Bearer ${options.apiKey || process.env.BUGRISK_API_KEY}`
          }
        }
      );
      
      console.log(response.data.quality_score);
      
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

program
  .command('report')
  .description('Generate report')
  .option('-p, --project <id>', 'Project ID')
  .option('-k, --api-key <key>', 'API Key')
  .option('-f, --format <format>', 'Report format (json, pdf, csv)', 'json')
  .option('-u, --url <url>', 'API URL', process.env.BUGRISK_API_URL || 'https://api.bugrisk.app')
  .action(async (options) => {
    const spinner = ora('Generating report...').start();
    
    try {
      const response = await axios.get(
        `${options.url}/report/${options.project}?format=${options.format}`,
        {
          headers: {
            'Authorization': `Bearer ${options.apiKey || process.env.BUGRISK_API_KEY}`
          }
        }
      );
      
      spinner.succeed('Report generated!');
      console.log(JSON.stringify(response.data, null, 2));
      
    } catch (error) {
      spinner.fail('Report generation failed');
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

program.parse();
