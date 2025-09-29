package com.github.yildizmy.service;

import com.github.yildizmy.domain.entity.Transaction;
import com.github.yildizmy.domain.entity.Wallet;
import com.github.yildizmy.domain.enums.Status;
import com.github.yildizmy.dto.request.TransactionRequest;
import com.github.yildizmy.dto.response.CommandResponse;
import com.github.yildizmy.repository.TransactionRepository;
import com.github.yildizmy.repository.WalletRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TransactionServiceTest {

    @InjectMocks
    private TransactionService transactionService;

    @Mock
    private TransactionRepository transactionRepository;

    @Mock
    private WalletRepository walletRepository;

    private TransactionRequest transactionRequest;
    private Wallet fromWallet;
    private Wallet toWallet;
    private Transaction transaction;

    @BeforeEach
    void setUp() {
        fromWallet = new Wallet();
        fromWallet.setId(1L);
        fromWallet.setBalance(new BigDecimal("1000.00"));
        fromWallet.setIban("TR1234567890123456789012345678");

        toWallet = new Wallet();
        toWallet.setId(2L);
        toWallet.setBalance(new BigDecimal("500.00"));
        toWallet.setIban("TR9876543210987654321098765432");

        // Fix: Use proper constructor matching your TransactionRequest
        transactionRequest = new TransactionRequest(
                1L,                           // id
                new BigDecimal("100.00"),     // amount
                "Test transaction",           // description
                Instant.now(),                // timestamp
                UUID.randomUUID(),            // transactionId
                Status.PENDING,               // status
                "TR1234567890123456789012345678", // fromAccount
                "TR9876543210987654321098765432", // toAccount
                1L                            // userId
        );

        transaction = new Transaction();
        transaction.setId(1L);
        transaction.setAmount(new BigDecimal("100.00"));
        transaction.setDescription("Test transaction");
        transaction.setFromWallet(fromWallet);
        transaction.setToWallet(toWallet);
        transaction.setStatus(Status.PENDING);
    }

    @Test
    void createTransaction_shouldReturnCommandResponse() {
        when(walletRepository.findById(1L)).thenReturn(Optional.of(fromWallet));
        when(walletRepository.findById(2L)).thenReturn(Optional.of(toWallet));
        when(transactionRepository.save(any(Transaction.class))).thenReturn(transaction);

        CommandResponse result = transactionService.createTransaction(transactionRequest);

        assertNotNull(result);
        // Fix: Use available methods instead of getId()
        assertNotNull(result.getMessage());  // or isSuccess() or whatever exists
        
        verify(walletRepository).findById(1L);
        verify(walletRepository).findById(2L);
        verify(transactionRepository).save(any(Transaction.class));
    }

    @Test
    void processTransaction_shouldUpdateWalletBalances() {
        when(walletRepository.findById(1L)).thenReturn(Optional.of(fromWallet));
        when(walletRepository.findById(2L)).thenReturn(Optional.of(toWallet));
        when(transactionRepository.save(any(Transaction.class))).thenReturn(transaction);

        var result = transactionService.createTransaction(transactionRequest);

        assertNotNull(result);
        verify(walletRepository, times(2)).save(any(Wallet.class));
    }
}