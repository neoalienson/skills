#!/usr/bin/env node

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

class CoverLetterGenerator {
  constructor(workspaceDir = '/home/neo/clawd') {
    this.workspaceDir = workspaceDir;
    this.coverLettersDir = join(workspaceDir, 'skills', 'cover-letter-generator', 'cover-letters');
    
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

    // Convert to PDF and save
    const filePath = join(this.coverLettersDir, filename);
    await this.convertToPDF(formattedLetter, filePath);

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
    return userSkills.filter(skill => 
      lowerJobDesc.includes(skill.toLowerCase())
    );
  }

  formatCoverLetter(content, companyName, jobTitle) {
    const date = new Date().toLocaleDateString('en-HK');
    
    return `
${this.userData.name}
${this.userData.address}
${this.userData.email} | ${this.userData.phone}

${date}

Hiring Manager
${companyName}
[Company Address]

Dear Hiring Manager,

${content.split('\n\n').slice(1).join('\n\n')}

Sincerely,
${this.userData.name}
    `.trim();
  }

  async convertToPDF(content, outputPath) {
    // For now, we'll create a simple text file as a placeholder
    // In a full implementation, this would use a PDF generation library
    const htmlContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    .header { text-align: left; margin-bottom: 30px; }
    .contact-info { margin-bottom: 20px; }
    .date { margin: 20px 0; }
    .salutation { margin: 20px 0; }
    .closing { margin: 20px 0 0 0; }
  </style>
</head>
<body>
  <div class="header">
    <div class="contact-info">${this.userData.name}<br>${this.userData.address}<br>${this.userData.email} | ${this.userData.phone}</div>
    <div class="date">${new Date().toLocaleDateString('en-HK')}</div>
    <div>Hiring Manager<br>${content.split('\n')[6] || 'Company Name'}</div>
  </div>
  <div class="salutation">Dear Hiring Manager,</div>
  ${content.split('\n\n').slice(1).map(p => `<p>${p}</p>`).join('')}
  <div class="closing">Sincerely,<br>${this.userData.name}</div>
</body>
</html>
    `;
    
    writeFileSync(outputPath.replace('.pdf', '.html'), htmlContent);
    
    // Try to convert HTML to PDF using wkhtmltopdf if available
    try {
      execSync(`wkhtmltopdf "${outputPath.replace('.pdf', '.html')}" "${outputPath}"`);
    } catch (error) {
      // If wkhtmltopdf is not available, create a text version
      console.log('wkhtmltopdf not found, creating text version');
      writeFileSync(outputPath.replace('.pdf', '.txt'), content);
    }
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
      const jobTitle = args[1] || 'Position';
      const companyName = args[2] || 'Company';

      if (!existsSync(jobDescFile)) {
        console.log(`Job description file not found: ${jobDescFile}`);
        process.exit(1);
      }

      const jobDescription = readFileSync(jobDescFile, 'utf8');

      generator.generateCoverLetter(jobDescription, jobTitle, companyName)
        .then(result => {
          console.log(`Cover letter generated successfully!`);
          console.log(`File saved to: ${result.filePath}`);
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