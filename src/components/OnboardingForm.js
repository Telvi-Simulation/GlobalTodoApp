import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import './OnboardingForm.css';

const WEBSITE_PURPOSE_OPTIONS = [
  'Portfolio',
  'E-commerce',
  'Blog',
  'Other',
];

const DESIGN_STYLE_OPTIONS = [
  'Modern',
  'Minimalist',
  'Professional',
];

const fullNameRegex = /^[A-Za-zÀ-ÖØ-öø-ÿ \-']{1,50}$/; // allow letters, spaces, hyphens, apostrophes, accented chars
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function sanitizeInput(value) {
  // Basic sanitization: trim and remove control chars
  return value.replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim();
}

export default function OnboardingForm({ onSubmit }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [websitePurpose, setWebsitePurpose] = useState('');
  const [designStyle, setDesignStyle] = useState('');
  const [additionalNotes, setAdditionalNotes] = useState('');

  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const validateField = (name, value) => {
    const val = sanitizeInput(value);
    switch (name) {
      case 'fullName':
        if (!val) return 'Full name is required.';
        if (!fullNameRegex.test(val)) return 'Full name must be 1-50 alphabetic characters, spaces, hyphens, or apostrophes.';
        return '';
      case 'email':
        if (!val) return 'Email address is required.';
        if (!emailRegex.test(val)) return 'Email address is invalid.';
        return '';
      case 'websitePurpose':
        if (!val) return 'Please select a website purpose.';
        if (!WEBSITE_PURPOSE_OPTIONS.includes(val)) return 'Invalid website purpose selected.';
        return '';
      case 'designStyle':
        if (!val) return 'Please select a preferred design style.';
        if (!DESIGN_STYLE_OPTIONS.includes(val)) return 'Invalid design style selected.';
        return '';
      case 'additionalNotes':
        if (val.length > 500) return 'Additional notes must be 500 characters or less.';
        return '';
      default:
        return '';
    }
  };

  const validateAll = () => {
    return {
      fullName: validateField('fullName', fullName),
      email: validateField('email', email),
      websitePurpose: validateField('websitePurpose', websitePurpose),
      designStyle: validateField('designStyle', designStyle),
      additionalNotes: validateField('additionalNotes', additionalNotes),
    };
  };

  const isFormValid = () => {
    const validationErrors = validateAll();
    return Object.values(validationErrors).every((err) => err === '');
  };

  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({ ...prev, [name]: validateField(name, value) }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    switch (name) {
      case 'fullName':
        setFullName(value);
        break;
      case 'email':
        setEmail(value);
        break;
      case 'websitePurpose':
        setWebsitePurpose(value);
        break;
      case 'designStyle':
        setDesignStyle(value);
        break;
      case 'additionalNotes':
        setAdditionalNotes(value);
        break;
      default:
        break;
    }
    // Clear error on change for better UX
    setErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validationErrors = validateAll();
    setErrors(validationErrors);
    setTouched({
      fullName: true,
      email: true,
      websitePurpose: true,
      designStyle: true,
      additionalNotes: true,
    });
    if (Object.values(validationErrors).every((err) => err === '')) {
      onSubmit({
        fullName: sanitizeInput(fullName),
        email: sanitizeInput(email),
        websitePurpose,
        designStyle,
        additionalNotes: sanitizeInput(additionalNotes),
      });
    }
  };

  return (
    <form className="onboarding-form" onSubmit={handleSubmit} noValidate>
      <div className="form-group">
        <label htmlFor="fullName">Full Name<span aria-hidden="true" className="required">*</span></label>
        <input
          type="text"
          id="fullName"
          name="fullName"
          value={fullName}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-describedby="fullName-error"
          aria-invalid={errors.fullName ? 'true' : 'false'}
          maxLength={50}
          required
          autoComplete="name"
        />
        {touched.fullName && errors.fullName && (
          <div className="error-message" id="fullName-error" role="alert">
            {errors.fullName}
          </div>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="email">Email Address<span aria-hidden="true" className="required">*</span></label>
        <input
          type="email"
          id="email"
          name="email"
          value={email}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-describedby="email-error"
          aria-invalid={errors.email ? 'true' : 'false'}
          required
          autoComplete="email"
        />
        {touched.email && errors.email && (
          <div className="error-message" id="email-error" role="alert">
            {errors.email}
          </div>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="websitePurpose">Website Purpose<span aria-hidden="true" className="required">*</span></label>
        <select
          id="websitePurpose"
          name="websitePurpose"
          value={websitePurpose}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-describedby="websitePurpose-error"
          aria-invalid={errors.websitePurpose ? 'true' : 'false'}
          required
        >
          <option value="" disabled>
            -- Select Purpose --
          </option>
          {WEBSITE_PURPOSE_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        {touched.websitePurpose && errors.websitePurpose && (
          <div className="error-message" id="websitePurpose-error" role="alert">
            {errors.websitePurpose}
          </div>
        )}
      </div>

      <fieldset className="form-group" aria-required="true" aria-describedby="designStyle-error">
        <legend>
          Preferred Design Style<span aria-hidden="true" className="required">*</span>
        </legend>
        {DESIGN_STYLE_OPTIONS.map((option) => (
          <div key={option} className="radio-option">
            <input
              type="radio"
              id={`designStyle-${option}`}
              name="designStyle"
              value={option}
              checked={designStyle === option}
              onChange={handleChange}
              onBlur={handleBlur}
              aria-invalid={errors.designStyle ? 'true' : 'false'}
              required
            />
            <label htmlFor={`designStyle-${option}`}>{option}</label>
          </div>
        ))}
        {touched.designStyle && errors.designStyle && (
          <div className="error-message" id="designStyle-error" role="alert">
            {errors.designStyle}
          </div>
        )}
      </fieldset>

      <div className="form-group">
        <label htmlFor="additionalNotes">Additional Notes (Optional)</label>
        <textarea
          id="additionalNotes"
          name="additionalNotes"
          value={additionalNotes}
          onChange={handleChange}
          onBlur={handleBlur}
          aria-describedby="additionalNotes-error"
          maxLength={500}
          rows={4}
        />
        {touched.additionalNotes && errors.additionalNotes && (
          <div className="error-message" id="additionalNotes-error" role="alert">
            {errors.additionalNotes}
          </div>
        )}
      </div>

      <button type="submit" disabled={!isFormValid()} className="submit-button">
        Continue
      </button>
    </form>
  );
}

OnboardingForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
};
