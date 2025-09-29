package com.github.yildizmy.service;

import com.github.yildizmy.domain.entity.User;
import com.github.yildizmy.domain.entity.Wallet;
import com.github.yildizmy.dto.request.WalletRequest;
import com.github.yildizmy.dto.response.WalletResponse;
import com.github.yildizmy.repository.UserRepository;
import com.github.yildizmy.repository.WalletRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class WalletServiceTest {

    @InjectMocks
    private WalletService walletService;

    @Mock
    private WalletRepository walletRepository;

    @Mock
    private UserRepository userRepository;

    private User user;
    private Wallet wallet;
    private WalletRequest walletRequest;

    @BeforeEach
    void setUp() {
        user = new User();
        user.setId(1L);
        user.setUsername("testuser");

        wallet = new Wallet();
        wallet.setId(1L);
        // Fix: Use correct setter method (setUser instead of setUserId)
        wallet.setUser(user);
        wallet.setIban("TR1234567890123456789012345678");
        wallet.setBalance(new BigDecimal("1000.00"));
        wallet.setName("Test Wallet");

        // Fix: Use proper constructor with all required parameters
        walletRequest = new WalletRequest(
                1L,                                   // id
                "TR1234567890123456789012345678",     // iban
                "Test Wallet",                        // name
                new BigDecimal("1000.00"),            // balance
                1L                                    // userId
        );
    }

    @Test
    void createWallet_shouldReturnWalletResponse() {
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));
        when(walletRepository.save(any(Wallet.class))).thenReturn(wallet);

        WalletResponse result = walletService.createWallet(walletRequest);

        assertNotNull(result);
        // Fix: Use correct getter method names
        assertEquals(1L, result.getId());           // Changed from id()
        assertEquals("TR1234567890123456789012345678", result.getIban()); // Changed from iban()

        verify(userRepository).findById(1L);
        verify(walletRepository).save(any(Wallet.class));
    }

    @Test
    void getWalletById_shouldReturnWalletResponse() {
        when(walletRepository.findById(1L)).thenReturn(Optional.of(wallet));

        WalletResponse result = walletService.getWalletById(1L);

        assertNotNull(result);
        // Fix: Use correct getter method names
        assertEquals(wallet.getIban(), result.getIban()); // Changed from iban()

        verify(walletRepository).findById(1L);
    }

    @Test
    void updateWallet_shouldReturnUpdatedWallet() {
        // Fix: Use proper constructor
        WalletRequest updateRequest = new WalletRequest(
                1L,                                   // id
                "TR9876543210987654321098765432",     // iban
                "Updated Wallet",                     // name
                new BigDecimal("2000.00"),            // balance
                1L                                    // userId
        );

        Wallet updatedWallet = new Wallet();
        updatedWallet.setId(1L);
        updatedWallet.setUser(user);
        updatedWallet.setIban("TR9876543210987654321098765432");
        updatedWallet.setName("Updated Wallet");
        updatedWallet.setBalance(new BigDecimal("2000.00"));

        when(walletRepository.findById(1L)).thenReturn(Optional.of(wallet));
        when(walletRepository.save(any(Wallet.class))).thenReturn(updatedWallet);

        WalletResponse result = walletService.updateWallet(1L, updateRequest);

        assertNotNull(result);
        assertEquals("Updated Wallet", result.getName());

        verify(walletRepository).findById(1L);
        verify(walletRepository).save(any(Wallet.class));
    }

    @Test
    void validateWalletConstraints_shouldWork() {
        // Fix: Use proper constructor for validation tests
        WalletRequest request1 = new WalletRequest(
                2L,
                "TR1111111111111111111111111111",
                "Validation Test Wallet 1",
                new BigDecimal("500.00"),
                2L
        );

        WalletRequest request2 = new WalletRequest(
                3L,
                "TR2222222222222222222222222222",
                "Validation Test Wallet 2",
                new BigDecimal("750.00"),
                3L
        );

        assertNotNull(request1);
        assertNotNull(request2);
        assertNotEquals(request1.getIban(), request2.getIban());
    }

    @Test
    void multipleWalletRequests_shouldWork() {
        WalletRequest request1 = new WalletRequest(
                4L,
                "TR3333333333333333333333333333",
                "Test Wallet 1",
                new BigDecimal("300.00"),
                4L
        );

        WalletRequest request2 = new WalletRequest(
                5L,
                "TR4444444444444444444444444444",
                "Test Wallet 2",
                new BigDecimal("400.00"),
                5L
        );

        assertNotNull(request1);
        assertNotNull(request2);
        assertNotEquals(request1.getId(), request2.getId());
    }
}