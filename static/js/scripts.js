function calculateTimeRemaining(deadline) {
    const deadlineDate = new Date(deadline);
    const now = new Date();
    const timeDiff = deadlineDate - now;

    if (timeDiff <= 0) {
        return 'Deadline passed';
    }

    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

    return `in about ${hours} hours, ${minutes} minutes, and ${seconds} seconds`;
}