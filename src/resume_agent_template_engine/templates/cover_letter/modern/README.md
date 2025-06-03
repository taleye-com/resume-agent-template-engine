# Modern Cover Letter Template

A professional, modern cover letter template with enhanced features including dynamic content generation, keyword optimization, and smart formatting.

## Features

### Design
- Clean, modern typography with professional color scheme
- Responsive layout that works on different page sizes
- Decorative elements that enhance visual appeal without being distracting
- Professional spacing and alignment

### Smart Content Processing
- **Dynamic Salutation Generation**: Automatically generates appropriate greetings based on recipient information
- **Keyword Enhancement**: Emphasizes relevant keywords from job descriptions when provided
- **Intelligent Address Formatting**: Handles various address formats and international addresses
- **Date Formatting**: Flexible date handling with automatic formatting

### Template Inheritance
- Built on the BaseTemplate class for inheritance support
- Modular block-based rendering system
- Extensible design for customization

### Macro Support
- Integration with the macro system for custom LaTeX commands
- Predefined macros for consistent formatting
- Automatic dependency resolution

## Required Data Fields

### Personal Information
```json
{
  "personalInfo": {
    "name": "Your Full Name",        // Required
    "email": "your.email@domain.com", // Required
    "phone": "+1 (555) 123-4567",     // Optional
    "address": {                      // Optional
      "street": "123 Main St",
      "city": "City",
      "state": "State",
      "zipCode": "12345",
      "country": "Country"
    }
  }
}
```

### Recipient Information
```json
{
  "recipient": {
    "company": "Company Name",        // Required
    "hiringManager": "Manager Name",  // Optional
    "position": "Position Title",     // Optional
    "address": {                      // Optional
      "street": "456 Business Ave",
      "city": "Business City",
      "state": "State",
      "zipCode": "67890"
    }
  }
}
```

### Content
```json
{
  "content": {
    "opening": "Opening paragraph text...",    // Required
    "body": [                                  // Required (array or string)
      "First body paragraph...",
      "Second body paragraph...",
      "Additional paragraphs..."
    ],
    "closing": "Closing paragraph text..."     // Required
  }
}
```

### Optional Enhancements
```json
{
  "date": "2024-01-15",              // Optional (defaults to current date)
  "jobInfo": {                       // Optional (for keyword enhancement)
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "description": "Job description text...",
    "requirements": ["requirement1", "requirement2"]
  }
}
```

## Usage Examples

### Basic Usage
```python
from resume_agent_template_engine import TemplateEngine

engine = TemplateEngine()

data = {
    "personalInfo": {
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "phone": "+1 (555) 123-4567"
    },
    "recipient": {
        "company": "Tech Corp Inc.",
        "hiringManager": "John Doe"
    },
    "content": {
        "opening": "I am writing to express my strong interest in the Software Engineer position at Tech Corp Inc.",
        "body": [
            "With over 5 years of experience in software development, I have developed expertise in Python, JavaScript, and cloud technologies that align perfectly with your requirements.",
            "In my previous role at Innovation Labs, I led a team that developed a microservices architecture serving over 1 million users, resulting in a 40% improvement in system performance."
        ],
        "closing": "I would welcome the opportunity to discuss how my experience and passion for technology can contribute to Tech Corp Inc.'s continued success."
    }
}

# Render to LaTeX
latex_content = engine.render_document("cover_letter", "modern", data)

# Export to PDF
pdf_path = engine.export_to_pdf("cover_letter", "modern", data, "output/cover_letter.pdf")
```

### Advanced Usage with Job Keywords
```python
data_with_keywords = {
    # ... basic data ...
    "jobInfo": {
        "keywords": ["Python", "Machine Learning", "AWS", "Agile", "Team Leadership"],
        "description": "Looking for a senior developer with Python and ML experience..."
    }
}

# The template will automatically emphasize matching keywords in the content
pdf_path = engine.export_to_pdf("cover_letter", "modern", data_with_keywords, "output/enhanced_cover_letter.pdf")
```

### Async PDF Generation
```python
# Submit for async processing
request_id = engine.export_to_pdf_async("cover_letter", "modern", data, "output/async_cover_letter.pdf")

# Check status
status = engine.get_build_status(request_id)
print(f"Build status: {status['status']}")

# Wait for completion
result = engine.wait_for_build(request_id, timeout=60)
if result['status'] == 'success':
    print(f"PDF generated: {result['output_path']}")
```

## Template Structure

The template is organized into modular blocks:

- **Header**: Contact information with modern styling
- **Date**: Formatted date block
- **Recipient**: Company and hiring manager information
- **Salutation**: Dynamic greeting generation
- **Body**: Main content with keyword enhancement
- **Closing**: Final paragraph
- **Signature**: Professional signature block

## Customization

### Color Scheme
The template uses a modern color palette defined in the LaTeX file:
- Primary Color: Blue (#2980b9)
- Secondary Color: Dark Gray (#34495e)
- Accent Color: Purple (#9b59b6)

You can customize colors by modifying the `\definecolor` commands in the template.

### Typography
The template uses modern typography settings:
- Font: Latin Modern (professional and readable)
- Line spacing: 1.15 for improved readability
- Paragraph spacing: 1.2em for clear separation

### Layout
- Margins: 1 inch on all sides
- Professional spacing between sections
- Decorative lines for visual appeal

## Template Inheritance

This template extends `BaseTemplate` and can be used as a parent for custom templates:

```python
from .modern.helper import ModernCoverLetterTemplate

class CustomCoverLetterTemplate(ModernCoverLetterTemplate):
    def _render_header_block(self, personal_info):
        # Custom header implementation
        return super()._render_header_block(personal_info)
```

## Validation

The template includes comprehensive data validation:
- Required field checking
- Email format validation
- Address format handling
- Content structure validation

Validation errors provide clear messages about missing or invalid data.

## Best Practices

1. **Content Length**: Keep body paragraphs concise (3-4 sentences each)
2. **Keywords**: Provide relevant job keywords for automatic enhancement
3. **Professional Tone**: Use formal language appropriate for business communication
4. **Customization**: Tailor content to specific companies and positions
5. **Proofreading**: Always review generated content before sending

## Troubleshooting

### Common Issues

1. **LaTeX Compilation Errors**
   - Ensure LaTeX is installed (TeX Live, MiKTeX, or MacTeX)
   - Check for special characters in content
   - Verify all required data fields are provided

2. **Font Issues**
   - Modern template uses Latin Modern fonts (included with LaTeX)
   - For custom fonts, ensure they're installed on the system

3. **PDF Generation Failures**
   - Check system LaTeX installation
   - Verify sufficient disk space for temporary files
   - Review error logs in the build results

### Performance Tips

1. Use async PDF generation for multiple documents
2. Enable caching for repeated builds
3. Validate data before submission to avoid failed builds

## Contributing

To extend this template:

1. Follow the existing code structure and patterns
2. Add appropriate validation for new features
3. Update documentation and examples
4. Test with various data inputs
5. Ensure compatibility with the macro system

## License

This template is part of the Resume AI Agent Template Engine and follows the same licensing terms. 