import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import OnboardingForm from '../../src/components/OnboardingForm';

describe('OnboardingForm', () => {
  const onSubmitMock = jest.fn();

  beforeEach(() => {
    onSubmitMock.mockClear();
  });

  test('renders all form fields', () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Website Purpose/i)).toBeInTheDocument();
    expect(screen.getByText(/Preferred Design Style/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Additional Notes/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Continue/i })).toBeDisabled();
  });

  test('validates and enables submit button on valid inputs', async () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);

    const fullNameInput = screen.getByLabelText(/Full Name/i);
    const emailInput = screen.getByLabelText(/Email Address/i);
    const websitePurposeSelect = screen.getByLabelText(/Website Purpose/i);
    const designStyleRadio = screen.getByLabelText(/Modern/i);
    const submitButton = screen.getByRole('button', { name: /Continue/i });

    fireEvent.change(fullNameInput, { target: { value: 'Anne-Marie O’Neill' } });
    fireEvent.blur(fullNameInput);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.blur(emailInput);
    fireEvent.change(websitePurposeSelect, { target: { value: 'Portfolio' } });
    fireEvent.blur(websitePurposeSelect);
    fireEvent.click(designStyleRadio);
    fireEvent.blur(designStyleRadio);

    await waitFor(() => expect(submitButton).toBeEnabled());

    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(onSubmitMock).toHaveBeenCalledWith({
        fullName: 'Anne-Marie O’Neill',
        email: 'user@example.com',
        websitePurpose: 'Portfolio',
        designStyle: 'Modern',
        additionalNotes: '',
      })
    );
  });

  test('shows error messages on blur invalid inputs', () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);

    const fullNameInput = screen.getByLabelText(/Full Name/i);
    fireEvent.blur(fullNameInput);
    expect(screen.getByText(/Full name is required/i)).toBeInTheDocument();

    fireEvent.change(fullNameInput, { target: { value: '1234' } });
    fireEvent.blur(fullNameInput);
    expect(
      screen.getByText(/Full name must be 1-50 alphabetic characters/i)
    ).toBeInTheDocument();

    const emailInput = screen.getByLabelText(/Email Address/i);
    fireEvent.change(emailInput, { target: { value: 'bademail' } });
    fireEvent.blur(emailInput);
    expect(screen.getByText(/Email address is invalid/i)).toBeInTheDocument();
  });

  test('rejects additional notes over 500 characters', () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);

    const notesInput = screen.getByLabelText(/Additional Notes/i);
    const longText = 'a'.repeat(501);
    fireEvent.change(notesInput, { target: { value: longText } });
    fireEvent.blur(notesInput);

    expect(
      screen.getByText(/Additional notes must be 500 characters or less/i)
    ).toBeInTheDocument();
  });

  test('does not submit with missing required fields', () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);
    const submitButton = screen.getByRole('button', { name: /Continue/i });
    expect(submitButton).toBeDisabled();

    fireEvent.click(submitButton);
    expect(onSubmitMock).not.toHaveBeenCalled();
  });

  test('sanitizes inputs by trimming and removing control chars', async () => {
    render(<OnboardingForm onSubmit={onSubmitMock} />);

    fireEvent.change(screen.getByLabelText(/Full Name/i), { target: { value: '  John Doe\u0007 ' } });
    fireEvent.change(screen.getByLabelText(/Email Address/i), { target: { value: 'john@example.com ' } });
    fireEvent.change(screen.getByLabelText(/Website Purpose/i), { target: { value: 'Blog' } });
    fireEvent.click(screen.getByLabelText(/Minimalist/i));

    const submitButton = screen.getByRole('button', { name: /Continue/i });

    await waitFor(() => expect(submitButton).toBeEnabled());

    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(onSubmitMock).toHaveBeenCalledWith(
        expect.objectContaining({
          fullName: 'John Doe',
          email: 'john@example.com',
        })
      )
    );
  });
});
