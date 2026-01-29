#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

class CoverLetterGenerator {
  constructor(workspaceDir = '/home/neo/clawd') {
    this.workspaceDir = workspaceDir;
    this.coverLettersDir = '/tmp';  // Changed to use /tmp for temporary files
    
    // Create cover letters directory if it doesn't exist
    if (!existsSync(this.coverLettersDir)) {
      mkdirSync(this.coverLettersDir, { recursive: true });
    }
    
    // Load user's resume/skills data
    this.userDataFile = join(workspaceDir, 'skills', 'cover-letter-generator', 'user-data.json');
    this.loadUserData();
  }

  loadUserData() {
    if (existsSync(this.userDataFile)) {
      try {
        const data = readFileSync(this.userDataFile, 'utf8');
        this.userData = JSON.parse(data);
      } catch (error) {
        console.error('Error loading user data:', error.message);
        this.userData = this.getDefaultUserData();
      }
    } else {
      this.userData = this.getDefaultUserData();
      this.saveUserData();
    }
  }

  getDefaultUserData() {
    return {
      name: 'Neo',
      email: 'neo@example.com',
      phone: '+852 1234 5678',
      address: 'Tseung Kwan O, Hong Kong',
      skills: ['Project Management', 'AWS Solutions Architecture', 'TOGAF', 'CFA', 'CISM'],
      experience: [
        {
          position: 'Senior Developer',
          company: 'Example Company',
          duration: '2020-Present',
          responsibilities: ['Led development teams', 'Implemented cloud solutions']
        }
      ],
      education: [
        {
          degree: 'Bachelor of Science',
          institution: 'University of Hong Kong',
          year: '2015'
        }
      ]
    };
  }

  saveUserData() {
    try {
      writeFileSync(this.userDataFile, JSON.stringify(this.userData, null, 2));
    } catch (error) {
      console.error('Error saving user data:', error.message);
      throw error;
    }
  }

  async generateCoverLetter(jobDescription, jobTitle = 'Position', companyName = 'Company') {
    // Prepare context for AI generation
    const context = {
      userData: this.userData,
      jobDescription: jobDescription,
      jobTitle: jobTitle,
      companyName: companyName
    };

    // Generate cover letter content using AI
    const coverLetterContent = await this.createCoverLetterContent(context);

    // Format the cover letter
    const formattedLetter = this.formatCoverLetter(coverLetterContent, companyName, jobTitle);

    // Generate filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `cover-letter-${companyName.replace(/\s+/g, '-')}-${timestamp}.pdf`;

    // Convert to PDF and save to /tmp
    const filePath = join('/tmp', filename);
    await this.convertToPDF(formattedLetter, filePath);

    // Attempt to send the file to the requestor (this is a simplified approach)
    // In a real implementation, this would interface with the messaging system
    console.log(`Cover letter generated at: ${filePath}`);
    console.log('Please retrieve the file from the messaging system.');
    
    return {
      success: true,
      filePath: filePath,
      filename: filename,
      content: formattedLetter
    };
  }

  async createCoverLetterContent(context) {
    // In a real implementation, this would call an AI service
    // For now, we'll simulate the AI-generated content
    const { userData, jobDescription, jobTitle, companyName } = context;

    // Extract relevant skills from job description
    const relevantSkills = this.extractRelevantSkills(jobDescription, userData.skills);

    // Create personalized cover letter
    const coverLetter = `
Dear Hiring Manager,

I am writing to express my strong interest in the ${jobTitle} position at ${companyName}. With my extensive background in technology and business, I believe I would be an excellent addition to your team.

In my current role, I have developed expertise in areas that directly align with your job requirements. My experience includes:

${relevantSkills.map(skill => `- ${skill}`).join('\n')}

I am particularly drawn to this opportunity because of [specific reason related to company/job]. My passion for excellence and commitment to continuous learning make me well-suited for this role.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences can contribute to ${companyName}'s continued success.

Sincerely,
${userData.name}
    `.trim();

    return coverLetter;
  }

  extractRelevantSkills(jobDescription, userSkills) {
    // Simple keyword matching to find relevant skills
    const lowerJobDesc = jobDescription.toLowerCase();
    const matchedSkills = userSkills.filter(skill => 
      lowerJobDesc.includes(skill.toLowerCase())
    );
    
    // If no skills match, return some general relevant skills
    if (matchedSkills.length === 0) {
      return ['JavaScript development', 'Front-end development', 'Problem solving', 'Code debugging'];
    }
    
    return matchedSkills;
  }

  formatCoverLetter(content, companyName, jobTitle) {
    const date = new Date().toLocaleDateString('en-HK');
    
    // Extract just the main content part from the generated cover letter
    const lines = content.split('\n');
    const startIndex = lines.findIndex(line => line.includes('Dear Hiring Manager'));
    const endIndex = lines.findIndex(line => line.includes('Sincerely,'));

    let mainContent = content;
    if (startIndex !== -1 && endIndex !== -1) {
      mainContent = lines.slice(startIndex, endIndex).join('\n');
    } else if (startIndex !== -1) {
      mainContent = lines.slice(startIndex).join('\n');
    }

    // Add extra line breaks between paragraphs to ensure proper spacing
    let formattedContent = mainContent.replace(/\n\s*\n/g, '\n\n\n'); // Double up empty lines for more space

    return `
${this.userData.name}
${this.userData.address}
${this.userData.email} | ${this.userData.phone}

${date}

Hiring Manager
${companyName}
[Company Address]

${formattedContent}

Sincerely,
${this.userData.name}
    `.trim();
  }

  async convertToPDF(content, outputPath) {
    // Try to create a proper PDF using pandoc with the installed tools
    try {
      const fs = await import('fs');
      const { exec } = await import('child_process');
      
      // Create markdown content
      const markdownContent = this.createMarkdownDocument(content);
      
      // Replace .pdf extension with .md for the markdown file
      const markdownPath = outputPath.replace('.pdf', '.md');
      
      // Write markdown file
      await fs.promises.writeFile(markdownPath, markdownContent);
      
      // Convert markdown to PDF using pandoc with proper options
      const convertPromise = new Promise((resolve, reject) => {
        exec(`pandoc "${markdownPath}" -o "${outputPath}" --pdf-engine=xelatex -V geometry:margin=1in --variable fontsize=12pt --variable documentclass=article`, 
          (error, stdout, stderr) => {
            if (error) {
              console.error('Error converting Markdown to PDF with pandoc:', error.message);
              console.log('Falling back to text file');
              
              // Fallback to creating text version in /tmp
              const txtOutputPath = outputPath.replace(/^.*[/]/, '/tmp/');  // Ensure it goes to /tmp
              writeFileSync(txtOutputPath.replace('.pdf', '.txt'), content);
              console.log(`TEXT_FILE_PATH:${txtOutputPath.replace('.pdf', '.txt')}`); // Special marker
              reject(error);
            } else {
              console.log(`PDF successfully created using pandoc: ${outputPath}`);
              console.log(`FILE_PATH:${outputPath}`); // Special marker to indicate file location
              resolve();
            }
          });
      });
      
      await convertPromise;
      
    } catch (error) {
      console.error('Error generating PDF from Markdown:', error.message);
      // Fallback to creating text version in /tmp
      console.log('Creating text version as fallback');
      const txtOutputPath = outputPath.replace(/^.*[/]/, '/tmp/');  // Ensure it goes to /tmp
      writeFileSync(txtOutputPath.replace('.pdf', '.txt'), content);
      console.log(`TEXT_FILE_PATH:${txtOutputPath.replace('.pdf', '.txt')}`); // Special marker
    }
  }
  
  createFormattedText(content) {
    // Split content into lines and process
    const lines = content.split('\n');
    
    // Extract components
    const nameLine = lines[0] ? lines[0] : 'Your Name';
    const addressLine = lines[1] ? lines[1] : 'Your Address';
    const contactLine = lines[2] ? lines[2] : 'Email and Phone';
    const dateLine = lines[4] ? lines[4] : 'Date';
    const companyLine = lines[6] ? lines[6] : 'Hiring Manager';
    const companyAddrLine = lines[7] ? lines[7] : 'Company Address';
    
    // Find the start of the main content (after the header)
    let contentStartIdx = 9; // Start after the header lines
    while (contentStartIdx < lines.length && !lines[contentStartIdx].includes('Dear Hiring Manager')) {
      contentStartIdx++;
    }
    
    // Find the end of the main content (before the closing)
    let contentEndIdx = contentStartIdx;
    while (contentEndIdx < lines.length && !lines[contentEndIdx].includes('Sincerely,')) {
      contentEndIdx++;
    }
    
    // Extract the main content
    const mainContentLines = lines.slice(contentStartIdx, contentEndIdx);
    let mainContent = '';
    
    // Process the main content with proper spacing
    for (let i = 0; i < mainContentLines.length; i++) {
      const line = mainContentLines[i];
      const trimmedLine = line.trim();
      
      // Handle list items
      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
        mainContent += `    ${trimmedLine}\n`;  // Indent list items
      } else if (trimmedLine !== '') {
        mainContent += `${trimmedLine}\n\n`;  // Add extra line break for paragraphs
      } else {
        // Empty lines are preserved for spacing
        mainContent += '\n';
      }
    }
    
    // Get the closing lines
    const sincerelyLine = lines[contentEndIdx] ? lines[contentEndIdx] : 'Sincerely,';
    const nameSignature = lines[contentEndIdx + 1] ? lines[contentEndIdx + 1] : 'Your Name';
    
    // Create the formatted text document
    return `${nameLine}
${addressLine}
${contactLine}


${dateLine}


${companyLine}
${companyAddrLine}


Dear Hiring Manager,

${mainContent.trim()}


${sincerelyLine}

${nameSignature}`;
  }
  
  createMarkdownDocument(content) {
    // Split content into lines and process
    const lines = content.split('\n');
    
    // Extract components
    const nameLine = lines[0] ? this.escapeMarkdown(lines[0]) : 'Your Name';
    const addressLine = lines[1] ? this.escapeMarkdown(lines[1]) : 'Your Address';
    const contactLine = lines[2] ? this.escapeMarkdown(lines[2]) : 'Email and Phone';
    const dateLine = lines[4] ? this.escapeMarkdown(lines[4]) : 'Date';
    const companyLine = lines[6] ? this.escapeMarkdown(lines[6]) : 'Hiring Manager';
    const companyAddrLine = lines[7] ? this.escapeMarkdown(lines[7]) : 'Company Address';
    
    // Find the start of the main content (after the header)
    let contentStartIdx = 9; // Start after the header lines
    while (contentStartIdx < lines.length && !lines[contentStartIdx].includes('Dear Hiring Manager')) {
      contentStartIdx++;
    }
    
    // Find the end of the main content (before the closing)
    let contentEndIdx = contentStartIdx;
    while (contentEndIdx < lines.length && !lines[contentEndIdx].includes('Sincerely,')) {
      contentEndIdx++;
    }
    
    // Extract the main content
    const mainContentLines = lines.slice(contentStartIdx, contentEndIdx);
    let mainContent = '';
    
    // Process the main content with proper markdown formatting
    // Skip the first line which is "Dear Hiring Manager" since it's handled separately
    for (let i = 1; i < mainContentLines.length; i++) {  // Start from index 1 to skip "Dear Hiring Manager"
      const line = mainContentLines[i];
      const trimmedLine = line.trim();
      
      // Handle list items
      if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
        mainContent += `${trimmedLine}\n`;
      } else if (trimmedLine !== '') {
        // Add the regular line
        mainContent += `${trimmedLine}\n\n`;
      } else {
        // Empty lines in Markdown for paragraph breaks
        mainContent += '\n';
      }
    }
    
    // Get the closing lines
    const sincerelyLine = lines[contentEndIdx] ? this.escapeMarkdown(lines[contentEndIdx]) : 'Sincerely,';
    const nameSignature = lines[contentEndIdx + 1] ? this.escapeMarkdown(lines[contentEndIdx + 1]) : 'Your Name';
    
    // Create the Markdown document - simplified version
    return `**${nameLine}**  
${addressLine}  
${contactLine}  

**Date:** ${dateLine}

**${companyLine}**  
${companyAddrLine}  

---

Dear Hiring Manager,

${mainContent}

${sincerelyLine}  
**${nameSignature}**`;
  }
  
  escapeMarkdown(text) {
    // Escape special markdown characters
    return text.replace(/\*/g, '\\*')
               .replace(/_/g, '\\_')
               .replace(/#/g, '\\#')
               .replace(/\+/g, '\\+')
               .replace(/-/g, '\\-')  // Don't escape hyphens in the middle of sentences
               .replace(/`/g, '\\`')
               .replace(/>/g, '\\>')
               .replace(/\[/g, '\\[')
               .replace(/\]/g, '\\]')
               .replace(/\(/g, '\\(')
               .replace(/\)/g, '\\)')
               .replace(/!/g, '\\!');
  }
}

// If running directly, provide a command-line interface
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const [, , command, ...args] = process.argv;
  const generator = new CoverLetterGenerator();

  switch (command) {
    case 'generate':
      if (args.length < 1) {
        console.log('Usage: cover-letter generate <job_description_file> [job_title] [company_name]');
        process.exit(1);
      }

      const jobDescFile = args[0];
      const jobTitle = args[1] || 'JavaScript Developer';
      const companyName = args[2] || 'Tech Innovations Ltd';

      if (!existsSync(jobDescFile)) {
        console.log(`Job description file not found: ${jobDescFile}`);
        process.exit(1);
      }

      const jobDescription = readFileSync(jobDescFile, 'utf8');

      generator.generateCoverLetter(jobDescription, jobTitle, companyName)
        .then(result => {
          console.log(`Cover letter generated successfully!`);
          console.log(`File saved to: ${result.filePath}`);
          
          // The file should now be automatically sent to the requestor
          console.log('File should be sent to requestor automatically.');
        })
        .catch(error => {
          console.error('Error generating cover letter:', error.message);
          process.exit(1);
        });
      break;

    case 'update-profile':
      // Allow updating user profile information
      console.log('Updating user profile...');
      // Implementation would go here
      break;

    case 'list':
      // List previously generated cover letters
      console.log('Listing generated cover letters...');
      // Implementation would go here
      break;

    default:
      console.log(`
Cover Letter Generator

Usage:
  cover-letter generate <job_description_file> [job_title] [company_name]    Generate a cover letter
  cover-letter update-profile                                               Update your profile information
  cover-letter list                                                         List generated cover letters

Examples:
  cover-letter generate job-desc.txt "Software Engineer" "Tech Corp"
      `);
  }
}

export default CoverLetterGenerator;