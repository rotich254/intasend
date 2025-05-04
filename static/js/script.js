// Script for handling payment form interactions
document.addEventListener('DOMContentLoaded', function () {
    const paymentForm = document.getElementById('payment-form');
    const amountInput = document.getElementById('amount');

    if (paymentForm) {
        paymentForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const amount = amountInput.value;
            if (amount <= 0) {
                alert('Please enter a valid amount');
                return;
            }

            // Submit the form if validation passes
            this.submit();
        });
    }
}); 